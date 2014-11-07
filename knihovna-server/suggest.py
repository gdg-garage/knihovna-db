# coding=utf-8
import logging
from google.appengine.ext import deferred
from admin import is_dev_server
from bigquery import BigQueryClient, BigQueryTable
from book_record import BookRecord
from google.appengine.ext import ndb
import datetime


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
            deferred.defer(start_bq_job, suggestions)
            suggestions.put()
            return suggestions
        elif not suggestions.completed:
            # Started, but still running.
            # TODO: restart if job_started too long ago
            return suggestions
        else:
            return suggestions


def start_bq_job(suggestions):
    assert isinstance(suggestions, SuggestionsRecord)
    item_ids = suggestions.key.string_id()
    logging.info("Start getting suggestions for item_ids '{}'.".format(
        item_ids
    ))
    bq = BigQueryClient()
    item_ids_array = item_ids.split('|')
    sql_item_ids = ', '.join(item_ids_array)  # 12|123 -> 12, 123
    query = SUGGESTION_QUERY.format(sql_item_ids)
    job_id = bq.create_query_job_async(query, item_ids)
    deferred.defer(check_bq_job, job_id, item_ids, suggestions,
                   _countdown=5)


def check_bq_job(job_id, item_ids, suggestions):
    bq = BigQueryClient()
    logging.info("Polling suggestion job {}.".format(job_id))
    json = bq.get_async_job_results(job_id, "", 2000)
    if not json['jobComplete']:
        deferred.defer(check_bq_job, job_id, item_ids, suggestions,
                       _countdown=5)
        return
    table = BigQueryTable(json)
    item_ids_array = item_ids.split('|')
    # Get the consolidated book for each item_id
    books = []
    for row in table.data:
        item_id = row[0]
        if item_id in item_ids_array:
            continue  # Original book.
        consolidated_book = BookRecord.query(
            BookRecord.item_id_array == item_id).get()
        if not consolidated_book:
            logging.info("No consolidated book with item_id '{}' found."
                         .format(item_id))
            continue
        if not consolidated_book in books:
            books.append(consolidated_book)
        if len(books) >= 1000:
            break
    suggestions.books = map(lambda br: br.key, books)
    suggestions.completed = True
    suggestions.put()
    logging.info("Suggestions for item_ids '{}' completed and saved.".format(
        item_ids
    ))


SUGGESTION_QUERY = """
/* Create prediction value by comparing borrow ratio of select audience with borrow ratio of everybody else. */
SELECT items_with_ratios.item_id as item_id,
       items_with_ratios.ratio / ratio_all.ratio as prediction
FROM [mlp.borrow_ratio_all] AS ratio_all
JOIN EACH (/* Compute ratio. */
           SELECT item_id,
                  RATIO_TO_REPORT(borrower_count) OVER (
                                                        ORDER BY borrower_count DESC) AS ratio
           FROM (/* Get other books borrowed by similar readers */
                 SELECT log_readers.item_id AS item_id,
                        COUNT(DISTINCT similar_reader_ids.user_id) AS borrower_count
                 FROM [mlp.log_generalized] AS log_readers
                 JOIN EACH (/* Get ids of users who have checked out the book. */
                            SELECT user_id
                            FROM [mlp.log_generalized]
                            WHERE item_id IN
                                ({})
                            GROUP BY user_id) AS similar_reader_ids ON log_readers.user_id = similar_reader_ids.user_id
                 GROUP BY item_id)) AS items_with_ratios ON items_with_ratios.item_id = ratio_all.item_id
JOIN EACH [mlp.tituly] AS metadata ON items_with_ratios.item_id = metadata.item_id
WHERE ratio_all.ratio > 0.002
ORDER BY prediction DESC
LIMIT 2000
"""

class SuggestionsRecord(ndb.Model):
    # item_ids of the original book is stored in key
    original_book = ndb.KeyProperty(indexed=False, kind=BookRecord)
    completed = ndb.BooleanProperty(indexed=False)
    job_started = ndb.DateTimeProperty(indexed=False)
    books = ndb.KeyProperty(repeated=True, indexed=False, kind=BookRecord)