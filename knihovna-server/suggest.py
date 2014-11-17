# coding=utf-8
import logging
import apiclient
from apiclient.errors import HttpError
from googleapiclient.errors import HttpError as gHttpError
from google.appengine.ext import deferred
from bigquery import BigQueryClient, BigQueryTable
from book_record import BookRecord
from google.appengine.ext import ndb
import datetime
import googleapiclient
from utils import is_dev_server


class Suggester(object):
    def __init__(self):
        pass

    def suggest(self, item_ids):
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
                job_started=job_started,
                books=[]
            )
            suggestions.put()
            deferred.defer(start_bq_job, key,
                           _countdown=1)
            return suggestions
        elif not suggestions.completed:
            # Started, but still running.
            # TODO: restart if job_started too long ago
            return suggestions
        else:
            return suggestions

BIGQUERY_JOB_ID_VER = "4"

def start_bq_job(suggestions_key):
    item_ids = suggestions_key.string_id()
    logging.info("Start getting suggestions for item_ids '{}'.".format(
        item_ids
    ))
    bq = BigQueryClient()
    item_ids_array = item_ids.split('|')
    sql_item_ids = ', '.join(item_ids_array)  # 12|123 -> 12, 123
    query = SUGGESTION_QUERY.format(sql_item_ids, sql_item_ids)
    job_id = "suggestions-{}-v{}".format('-'.join(item_ids_array),
                                         BIGQUERY_JOB_ID_VER)
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
    json = bq.get_async_job_results(job_id, page_token,
                                    MAX_RESULTS_PER_SUGGESTIONS_QUERY)
    if not json['jobComplete']:
        logging.info("- job not completed yet.")
        deferred.defer(check_bq_job, job_id, item_ids, suggestions_key, "",
                       _countdown=5)
        return
    table = BigQueryTable(json)
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
    next_page_token = json.get('pageToken', "")
    if next_page_token != "":
        suggestions.put()
        deferred.defer(check_bq_job, job_id, item_ids, suggestions_key,
                       next_page_token)
        logging.info("Suggestions for item_ids '{}' partly fetched. "
                     "Running again.".format(item_ids))
    else:
        suggestions.completed = True
        suggestions.put()
        logging.info("Suggestions for item_ids '{}' completed and saved.".format(
            item_ids
        ))


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
    LIMIT 1200
"""

class SuggestionsRecord(ndb.Model):
    # item_ids of the original book is stored in key
    original_book = ndb.KeyProperty(indexed=False, kind=BookRecord)
    completed = ndb.BooleanProperty(indexed=False)
    job_started = ndb.DateTimeProperty(indexed=False)
    # A sorted array of BookRecord keys that are suggestion for [original_book]
    books = ndb.KeyProperty(repeated=True, indexed=False, kind=BookRecord)
    # A sorted array of prediction probability values. Index corresponds to
    # index in [books], so books[i] has a prediction prob. of
    # books_prediction[i].
    books_prediction = ndb.FloatProperty(repeated=True, indexed=False)
