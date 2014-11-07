# coding=utf-8
import logging
import os
from datetime import datetime

from google.appengine.ext import ndb
import webapp2
from google.appengine.ext import deferred

from book_consolidation import _ConsolidatedBooksData, consolidate_books
from jinja import render_html
from bigquery import BigQueryClient, BigQueryTable
from autocompleter import Autocompleter, BookRecord


class AdminPage(webapp2.RequestHandler):
    def get(self):
        render_html(self, "admin_welcome.html", u"Tisíc knih admin",
                    u"<p>Vítej, poutníče!</p>",
                    template_values={"links": [
                        ("Test BigQuery", "/admin/test/bq/"),
                        ("Test Autocomplete", "/admin/test/autocomplete/"),
                        ("Update Autocomplete From BigQuery",
                         '/admin/update_autocomplete/')
                    ]})


class TestAutocomplete(webapp2.RequestHandler):
    def get(self):
        result = u"<p>Behold autocomplete stuff:</p>"
        autocompleter = Autocompleter()
        query = self.request.get('q', default_value=u"Tolkien")
        suggestions = autocompleter.get_results(query)
        result += u"<pre>"
        for suggestion in suggestions:
            assert isinstance(suggestion, BookRecord)
            result += u"{} - {} ({})\n".format(suggestion.author, suggestion.title, suggestion.year)
        result += u"</pre>"

        render_html(self, "admin_generic.html", u"Testing BQ",
                    result)


class UpdateAutocompleteFromBigQuery(webapp2.RequestHandler):
    def get(self):
        logging.info("Starting task to update autocomplete from BigQuery")
        deferred.defer(init_autocomplete_updating)
        self.redirect("/admin/")


def init_autocomplete_updating():
    bq = BigQueryClient()
    query = ALL_BOOKS_QUERY
    if is_dev_server():
        logging.info("We are in dev_server.")
        query += " LIMIT 2000"
    job_id = 'autocomplete-big-update-{}'.format(
        int((datetime.now()-datetime.utcfromtimestamp(0)).total_seconds())
    )
    logging.info("Creating new autocomplete update job: {}".format(job_id))
    bq.create_query_job_async(query, job_id)
    deferred.defer(check_autocomplete_update_job_done, job_id, 1000, "",
                   _countdown=5)


def check_autocomplete_update_job_done(job_id,
                                       max_results,
                                       page_token):
    bq = BigQueryClient()
    logging.info("Polling autocomplete update job (pageToken={}).".format(
        page_token
    ))
    json = bq.get_async_job_results(job_id,
                                    page_token,
                                    max_results)
    if json['jobComplete']:
        # Job is complete, we have payload.
        logging.info("- job is complete")
        next_page_token = json.get('pageToken', "")
        new_data = BigQueryTable(json).data
        logging.info("- we have {} new rows".format(len(new_data)))
        data_record = _AutocompleteUpdateJobRawData(
            rows=new_data
        )
        data_record.put()
        if next_page_token != "":
            # Run again
            logging.info("- running next round with token {}".format(next_page_token))
            deferred.defer(check_autocomplete_update_job_done,
                           job_id, max_results,
                           next_page_token,
                           _countdown=5)
        else:
            logging.info("- we have the whole dataset")
            deferred.defer(parse_autocomplete_update_data,
                           _countdown=5)
    else:
        logging.info("- job isn't complete yet")
        deferred.defer(check_autocomplete_update_job_done,
                       job_id, max_results, "",
                       _countdown=10)


class _AutocompleteUpdateJobRawData(ndb.Model):
    rows = ndb.JsonProperty(indexed=False)


def parse_autocomplete_update_data():
    past_data_records = _AutocompleteUpdateJobRawData.query().fetch(1000)
    if len(past_data_records) >= 1000:
        logging.warning("There are more than 1000 data records.")
    past_data = []
    for data_record in past_data_records:
        assert isinstance(data_record, _AutocompleteUpdateJobRawData)
        past_data.append(data_record.rows)
    # flatten data
    data = [item for sublist in past_data for item in sublist]
    autocompleter = Autocompleter()
    books = consolidate_books(data)
    docs = []
    records = []
    for book in books:
        assert isinstance(book, _ConsolidatedBooksData)
        doc, record = Autocompleter.create_instances_to_be_saved(
            book.item_ids,
            book.author,
            book.title,
            book.year,
            book.count
        )
        docs.append(doc)
        if len(docs) >= 200:
            autocompleter.index.put(docs)
            logging.info("{} docs were put into index".format(len(docs)))
            docs = []
        records.append(record)
        if len(records) >= 100:
            ndb.put_multi(records)
            logging.info(
                "{} records were put into storage".format(len(records)))
            records = []
    autocompleter.index.put(docs)
    logging.info("{} docs were put into index".format(len(docs)))
    ndb.put_multi(records)
    logging.info("{} records were put into storage".format(len(records)))
    ndb.delete_multi([m.key for m in past_data_records])

ALL_BOOKS_QUERY = """
    SELECT
      tituly.item_id as item_id,
      tituly.author as author,
      tituly.title as title,
      tituly.year as year,
      COUNT(log.item_id) AS cnt
    FROM
      [mlp.log_generalized] as log
    JOIN
      EACH [mlp.tituly] AS tituly
    ON
      tituly.item_id = log.item_id
    # WHERE
      # Guard against old books getting more count due to being there longer.
      # log.vypujcky_when > '2013-01-01 00:00:00 UTC'
    GROUP BY
      item_id, author, title, year
    HAVING
      # Control against obscure books and potentially personally identifiable books.
      cnt >= 50
    ORDER BY cnt DESC
"""


class TestBqPage(webapp2.RequestHandler):
    def get(self):
        result = u"<p>Behold a query from BigQuery:</p>"
        bq = BigQueryClient()
        job = bq.create_query_job("SELECT author FROM [mlp.tituly] "
                                  "WHERE NOT author CONTAINS '0' LIMIT 1000")
        json = job.execute()
        result += u"<pre>"
        result += u"{}".format(json)
        result += u"</pre>"
        table = BigQueryTable(json)
        for row in table.data:
            result += u"<p>{}</p>".format(row[0])
        # for row in json['rows']:
        #     result += u"<p>{}</p>".format(row['f'][0]['v'])


        render_html(self, "admin_generic.html", u"Testing BQ",
                    result)

def is_dev_server():
    if os.environ['SERVER_SOFTWARE'].find('Development') == 0:
        return True
    else:
        return False

application = webapp2.WSGIApplication([
    ('/admin/', AdminPage),
    ('/admin/test/bq/', TestBqPage),
    ('/admin/test/autocomplete/', TestAutocomplete),
    ('/admin/update_autocomplete/', UpdateAutocompleteFromBigQuery)
], debug=True)