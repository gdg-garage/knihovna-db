# coding=utf-8
from google.appengine.ext import ndb

import webapp2
from jinja import render_html
from bigquery import BigQueryClient, BigQueryTable
from autocompleter import Autocompleter, BookRecord
import logging
from google.appengine.ext import deferred

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
    WHERE
      # Guard against old books getting more count due to being there longer.
      log.vypujcky_when > '2013-01-01 00:00:00 UTC'
    GROUP BY
      item_id, author, title, year
    HAVING
      cnt >= 50  # Control against obscure books and potentially personally identifiable books.
    ORDER BY cnt DESC
"""


def consolidate_books(table):
    assert isinstance(table, BigQueryTable)
    books = []
    ignore_rows = []
    for i in range(table.nrows):
        if i % 50 == 0:
            logging.info("Consolidating books: row {}/{}".format(
                i, table.nrows
            ))
        if i in ignore_rows:
            continue
        row = table.data[i]
        item_ids = [row[0]]
        author = row[1]
        title = row[2]
        years = [row[3]]
        counts = [int(row[4])]
        author_and_title = u"{}//{}".format(author, title)
        for j in range(i + 1, table.nrows):
            row2 = table.data[j]
            other_author_and_title = u"{}//{}".format(row2[1], row2[2])
            if author_and_title != other_author_and_title:
                continue
            ignore_rows.append(j)
            item_ids.append(row2[0])
            years.append(row2[3])
            counts.append(int(row2[4]))
        year = None
        for year_str in years:
            try:
                year_candidate = int(unicode(year_str))
                if not year or year_candidate > year:
                    year = year_candidate
            except:
                pass
        count = 0
        prev_count_str = ""
        counts.sort(reverse=True)
        for count_str in counts:
            count_str = unicode(count_str)
            if count_str == prev_count_str:
                continue  # Exactly the same counts are suspicious
            count += int(count_str)
            prev_count_str = count_str
        book = _ConsolidatedBooksData(
            item_ids='|'.join(item_ids),
            author=author,
            title=title,
            year=year,
            count=count
        )
        books.append(book)
        logging.info(u"Book '{}' consolidated into item_ids='{}'.".format(
            author_and_title, book.item_ids
        ))
    logging.info("Consolidating books: done ({} books from {} rows)".format(
        len(books), table.nrows
    ))
    return books




class _ConsolidatedBooksData(object):
    def __init__(self, item_ids, author, title, year, count):
        self.item_ids = item_ids
        self.author = author
        self.title = title
        self.year = year
        self.count = count



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


application = webapp2.WSGIApplication([
    ('/admin/', AdminPage),
    ('/admin/test/bq/', TestBqPage),
    ('/admin/test/autocomplete/', TestAutocomplete),
    ('/admin/update_autocomplete/', UpdateAutocompleteFromBigQuery)
], debug=True)