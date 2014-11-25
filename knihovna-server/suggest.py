# coding=utf-8
import logging
import datetime

from third_party.apiclient.errors import HttpError
from google.appengine.ext import deferred
from google.appengine.ext import ndb

from third_party.googleapiclient.errors import HttpError as gHttpError
from bigquery import BigQueryClient, BigQueryTable
from book_record import BookRecord

import uuid
import json


class Suggester(object):
    VERSION = 1

    def __init__(self):
        pass

    @staticmethod
    def _no_suggestions_yet(item_ids, job_started, status="started"):
        original_book_key = ndb.Key(BookRecord, item_ids)
        original_book = original_book_key.get()
        json_object = {
            'version': Suggester.VERSION,
            'item_ids': item_ids,
            'job_started': job_started.isoformat(),
            'status': status
        }
        json_object['original_book'] = {
            'author': original_book.author,
            'title': original_book.title,
            'year': original_book.year
        }
        return json.dumps(json_object, indent=2)

    def get_json(self, item_ids):
        key = ndb.Key(SuggestionsRecord, item_ids)
        suggestions = key.get()
        if not suggestions:
            # Not even started yet
            original_book_key = ndb.Key(BookRecord, item_ids)
            job_started = datetime.datetime.now()
            suggestions = SuggestionsRecord(
                key=key,
                original_book=original_book_key,
                completed=False,
                version=Suggester.VERSION,
                job_started=job_started,
                books=[],
                json=None,
                json_generation_started=False
            )
            suggestions.put()
            deferred.defer(start_bq_job, key,
                           _countdown=1)
            logging.info("Suggester returns NO_SUGGESTIONS_YET for {} because "
                         "this is the first time we see this."
                         .format(item_ids))
            return Suggester._no_suggestions_yet(item_ids, job_started)

        assert isinstance(suggestions, SuggestionsRecord)
        if not suggestions.completed:
            # Started, but still running.
            logging.info("Suggester returns NO_SUGGESTIONS_YET for {} because "
                         "job is in progress."
                         .format(item_ids))
            return Suggester._no_suggestions_yet(item_ids,
                                                 suggestions.job_started)

        elif not suggestions.json:
            # Completed, but JSON is not available.
            if not suggestions.json_generation_started:
                # JSON creation hasn't even started yet
                suggestions.json_generation_started = True
                suggestions.put()
                deferred.defer(create_suggestions_json, suggestions.key)
                logging.info("Started creating JSON for {}".format(item_ids))
            logging.info("Suggester returns NO_SUGGESTIONS_YET for {} because "
                         "JSON is not yet generated."
                         .format(item_ids))
            return Suggester._no_suggestions_yet(item_ids,
                                                 suggestions.job_started,
                                                 status="generating_json")

        else:
            logging.info("Suggester returns JSON for {}"
                         .format(item_ids))
            return suggestions.json


def start_bq_job(suggestions_key):
    item_ids = suggestions_key.string_id()
    logging.info("Start getting suggestions for item_ids '{}'.".format(
        item_ids
    ))
    bq = BigQueryClient()
    item_ids_array = item_ids.split('|')
    sql_item_ids = ', '.join(item_ids_array)  # 12|123 -> 12, 123
    query = SUGGESTION_QUERY.format(sql_item_ids, sql_item_ids)
    job_id = "suggestions-{}".format(str(uuid.uuid4()))
    try:
        bq.create_query_job_async(query, job_id)
    except (HttpError, gHttpError) as e:
        logging.error(u"HttpError received when trying to crete new job {}. "
                      u"{}"
                      u"Possible cause: job was created in the past 24 hours."
                      u"Let's check it.".format(job_id, e))

    deferred.defer(check_bq_job, job_id, item_ids, suggestions_key, "",
                   _countdown=5)

MAX_RESULTS_PER_SUGGESTIONS_QUERY = 600


def check_bq_job(job_id, item_ids, suggestions_key, page_token):
    bq = BigQueryClient()
    logging.info("Polling suggestion job {}.".format(job_id))
    # TODO: catch 404 errors for jobs created 24+ hours ago, retry with new jobid
    try:
        bq_json = bq.get_async_job_results(job_id, page_token,
                                           MAX_RESULTS_PER_SUGGESTIONS_QUERY)
    except (HttpError, gHttpError) as e:
        logging.error("Error from BigQuery with item_id={}.".format(item_ids))
        raise deferred.PermanentTaskFailure(e)
    if not bq_json['jobComplete']:
        logging.info("- job not completed yet.")
        deferred.defer(check_bq_job, job_id, item_ids, suggestions_key, "",
                       _countdown=5)
        return
    if not 'rows' in bq_json:
        logging.error(u"Invalid json for BigQueryTable. Job for {} is probably "
                      u"invalid (bad item_id?).\n"
                      u"JSON:\n"
                      u"{}".format(item_ids, bq_json))
        raise deferred.PermanentTaskFailure("No rows in BigQuery response for "
                                            "{}.".format(item_ids))
    table = BigQueryTable(bq_json)
    item_ids_array = item_ids.split('|')
    # Get the consolidated book for each item_id
    suggestions = suggestions_key.get()
    assert isinstance(suggestions, SuggestionsRecord)
    for row in table.data:
        item_id = row[0]
        prediction = float(row[1])
        if item_id in item_ids_array:
            continue  # Original book.
        consolidated_book_key = BookRecord.query(
            BookRecord.item_id_array == item_id).get(keys_only=True)
        if not consolidated_book_key:
            logging.info("No consolidated book with item_id '{}' found."
                         .format(item_id))
            continue
        if not consolidated_book_key in suggestions.books:
            suggestions.books.append(consolidated_book_key)
            suggestions.books_prediction.append(prediction)
        if len(suggestions.books) >= 1000:
            break
    next_page_token = bq_json.get('pageToken', "")
    if next_page_token != "" and len(suggestions.books) < 1000:
        suggestions.put()
        deferred.defer(check_bq_job, job_id, item_ids, suggestions_key,
                       next_page_token)
        logging.info("Suggestions for item_ids '{}' partly fetched. "
                     "Running again.".format(item_ids))
    else:
        suggestions.completed = True
        suggestions.json_generation_started = True
        suggestions.put()
        logging.info("Suggestions for item_ids '{}' completed and saved.".format(
            item_ids
        ))
        deferred.defer(create_suggestions_json, suggestions.key)


def create_suggestions_json(suggestions_key):
    suggestions = suggestions_key.get()
    item_ids = suggestions.key.string_id()
    assert isinstance(suggestions, SuggestionsRecord)
    if not suggestions.completed:
        logging.warning("create_suggestions_json for {} called although "
                        "suggestions are still not completed.".format(item_ids))
        # deferred.defer(create_suggestions_json, suggestions_key,
        #                _countdown=3)
        return
    json_object = {
        'version': Suggester.VERSION,
        'item_ids': item_ids,
        'job_started': suggestions.job_started.isoformat()
    }
    original_book = suggestions.original_book.get()
    if not original_book:
        raise deferred.PermanentTaskFailure("Original book not found for {} "
                                            "when creating JSON."
                                            .format(item_ids))
    assert isinstance(original_book, BookRecord)
    json_object['original_book'] = {
        'author': original_book.author,
        'title': original_book.title,
        'year': original_book.year
    }
    json_object['status'] = 'completed'
    json_object['suggestions'] = []
    book_records = ndb.get_multi(suggestions.books)
    assert len(book_records) == len(suggestions.books_prediction)
    for i in xrange(len(book_records)):
        book = book_records[i]
        assert isinstance(book, BookRecord)
        json_object['suggestions'].append({
            'author': book.author,
            'title': book.title,
            'item_ids': book.key.string_id(),
            'prediction': suggestions.books_prediction[i]
        })
    precomputed_json = json.dumps(json_object, indent=2)
    suggestions.json = precomputed_json
    suggestions.put()
    logging.info("Created and saved JSON for {}".format(item_ids))


SUGGESTION_QUERY = """
    SELECT books_borrowed_by_similar_users.item_id AS item_id,
           COUNT(DISTINCT user_id) / sum_all_similar_users.value / ratio_all.ratio AS prediction
    FROM [mlp.user_item_pairs_books_only] AS books_borrowed_by_similar_users
    JOIN EACH [mlp.books_ratio_all] AS ratio_all ON books_borrowed_by_similar_users.item_id = ratio_all.item_id
    CROSS JOIN ( /* Sum users who also borrowed this book. */
                SELECT COUNT(DISTINCT user_id) AS value
                FROM [mlp.user_item_pairs_books_only]
                WHERE item_id IN ({}) ) AS sum_all_similar_users
    WHERE user_id IN ( /* Users who also borrowed this book. */
                      SELECT user_id
                      FROM [mlp.user_item_pairs_books_only]
                      WHERE item_id IN ({}) )
      AND ratio_all.ratio > 0.0001
      # AND cnt > 5
    GROUP BY item_id,
             sum_all_similar_users.value,
             ratio_all.ratio
    ORDER BY prediction DESC
    LIMIT 1800
"""


class SuggestionsRecord(ndb.Model):
    # item_ids of the original book is stored in key
    original_book = ndb.KeyProperty(indexed=False, kind=BookRecord)
    completed = ndb.BooleanProperty()
    version = ndb.IntegerProperty()
    job_started = ndb.DateTimeProperty(indexed=False)
    # A sorted array of BookRecord keys that are suggestion for [original_book]
    books = ndb.KeyProperty(repeated=True, indexed=False, kind=BookRecord)
    # A sorted array of prediction probability values. Index corresponds to
    # index in [books], so books[i] has a prediction prob. of
    # books_prediction[i].
    books_prediction = ndb.FloatProperty(repeated=True, indexed=False)
    # Precomputed JSON for a SuggestionsRecord so that we don't need to construct
    # it every time.
    json = ndb.TextProperty()
    json_generation_started = ndb.BooleanProperty()