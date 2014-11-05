# coding=utf-8

import webapp2
from jinja import render_html
from google.appengine.api import search
from bigquery import BigQueryClient, ALL_BOOKS_QUERY

class AdminPage(webapp2.RequestHandler):
    def get(self):
        render_html(self, "admin_welcome.html", u"Tisíc knih admin",
                    u"<ol>"
                    u"<li><a href='/admin/test_bq/'>Test BQ connection</a></li>"
                    u"</ol>")


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
        for row in json['rows']:
            result += u"<p>{}</p>".format(row['f'][0]['v'])

        render_html(self, "admin_welcome.html", u"Testing BQ",
                    result)


application = webapp2.WSGIApplication([
    ('/admin/', AdminPage),
    ('/admin/test_bq/', TestBqPage)
], debug=True)