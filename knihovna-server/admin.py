# coding=utf-8
import logging
import os

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
        deferred.defer(run_autocomplete_updating)
        self.redirect("/admin/")


def run_autocomplete_updating():
    autocompleter = Autocompleter()
    bq = BigQueryClient()
    query = ALL_BOOKS_QUERY
    if is_dev_server():
        logging.info("We are in dev_server.")
        query += " LIMIT 1000"
    job = bq.create_query_job(query, timeout_ms=30000)
    json = job.execute()
    table = BigQueryTable(json)
    books = consolidate_books(table)
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