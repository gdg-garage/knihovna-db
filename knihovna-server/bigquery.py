# coding=utf-8

import httplib2

from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials

class BigQueryClient(object):
    # BigQuery API Settings
    SCOPE = 'https://www.googleapis.com/auth/bigquery'
    PROJECT_NUMBER = '1089267425611'

    def __init__(self):
        # Create a new API service for interacting with BigQuery
        credentials = AppAssertionCredentials(scope=BigQueryClient.SCOPE)
        http = credentials.authorize(httplib2.Http())
        self.service = build('bigquery', 'v2', http=http)

    def create_query_job(self, query, timeout_ms=10000):
        """
        Constructs a query job that can be then run with execute()
        :param query: The SQL query string.
        :param timeout_ms:
        :return: The job.
        """
        query_config = {
            'query': query,
            'timeoutMs': timeout_ms
        }
        return self.service.jobs()\
            .query(projectId=BigQueryClient.PROJECT_NUMBER, body=query_config)



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