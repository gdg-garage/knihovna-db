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


class BigQueryTable(object):
    """
    Copies data from a BigQuery json result into more pythonic data structure.
    """
    def __init__(self, json):
        self.ncols = len(json['schema']['fields'])
        self.nrows = len(json['rows'])
        self.data = []
        for i in range(self.nrows):
            self.data.append(BigQueryTable.get_row(i, json))

    @staticmethod
    def get_row(i, json):
        result = []
        raw_row = json['rows'][i]
        for raw_value in raw_row['f']:
            value = raw_value['v']
            result.append(value)
        return result


