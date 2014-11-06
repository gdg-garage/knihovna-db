# coding=utf-8

from unidecode import unidecode
from google.appengine.api import search
from google.appengine.ext import ndb


class Autocompleter(object):
    def __init__(self):
        self.index = search.Index(name='book_autocomplete')

    def get_results(self, query):
        query_ascii = unidecode(query)
        results = self.index.search(
            query=search.Query('tokens:{}'.format(query_ascii),
                options=search.QueryOptions(limit=5,
                    sort_options=search.SortOptions(
                        expressions=[search.SortExpression(expression='count_log')],
                        limit=1000)
                    #returned_fields=['author', 'subject', 'summary'],
                    #snippeted_fields=['content']
              )))
        assert(isinstance(results, search.SearchResults))
        datastore_results = []
        for search_result in results.results:
            assert(isinstance(search_result, search.ScoredDocument))
            key = ndb.Key('BookRecord', search_result.doc_id)
            datastore_record = key.get()
            datastore_results.append(datastore_record)
        return datastore_results

    def add(self, item_id, author, title, year, count):
        document, record = Autocompleter.create_instances_to_be_saved(
            item_id, author, title, year, count
        )
        self.index.put(document)
        record.put()

    @staticmethod
    def create_instances_to_be_saved(item_id, author, title, year, count):
        """
        A method that returns saveable objects without actually saving them.
        This allows batching saves.
        :param item_id: String with unique item id.
        :param author:
        :param title:
        :param year:
        :param count: Count. Will be forced to an integer if it isn't already.
        :return: a tuple of document (Search API) and record (NDB)
        """
        document = Autocompleter._create_document(item_id, author, title,
                                                  count)
        record = Autocompleter._create_record(item_id, author, title,
                                              year, count)
        return document, record


    @staticmethod
    def _create_record(item_id, author, title, year, count):
        key = ndb.Key('BookRecord', item_id)
        datastore_record = BookRecord(
            key=key,
            author=author,
            title=title,
            year=year,
            count=count
        )
        return datastore_record


    @staticmethod
    def _create_document(item_id, author, title, count):
        author_ascii = unidecode(author)
        title_ascii = unidecode(title)
        phrase = "{} {}".format(author_ascii, title_ascii)
        tokens = ','.join(Autocompleter.tokenize_autocomplete(phrase))
        document = search.Document(
            doc_id=item_id,
            fields=[
                search.TextField(name='tokens', value=tokens),
                search.NumberField(name='count_log', value=count)
            ]
        )
        return document


    @staticmethod
    def tokenize_autocomplete(phrase):
        a = []
        for word in phrase.split():
            j = 1
            while True:
                for i in range(len(word) - j + 1):
                    a.append(word[i:i + j])
                if j == len(word):
                    break
                j += 1
        return a


class BookRecord(ndb.Model):
    item_id = ndb.StringProperty()
    author = ndb.StringProperty()
    title = ndb.StringProperty()
    year = ndb.IntegerProperty()
    count = ndb.IntegerProperty()
