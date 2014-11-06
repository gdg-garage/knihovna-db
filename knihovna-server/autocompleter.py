# coding=utf-8
import logging

from unidecode import unidecode
from google.appengine.api import search
from google.appengine.ext import ndb
import re

class Autocompleter(object):
    def __init__(self):
        self.index = search.Index(name='book_autocomplete')

    SANITIZE_PATTERN = re.compile("[^a-zA-Z_0-9 ]")

    def get_results(self, query):
        query_ascii = unidecode(query)
        query_ascii = Autocompleter.SANITIZE_PATTERN.sub("", query_ascii)

        logging.info("Autocomplete search for '{}' (sanitized to '{}').".format(
            query, query_ascii
        ))

        results = self.index.search(
            query=search.Query('tokens:({})'.format(query_ascii),
                options=search.QueryOptions(limit=5,
                                            ids_only=True)
            )
        )
        logging.info("Got {} results.".format(len(results.results)))
        assert(isinstance(results, search.SearchResults))
        list_of_keys = []
        for search_result in results.results:
            assert(isinstance(search_result, search.ScoredDocument))
            key = ndb.Key('BookRecord', search_result.doc_id)
            list_of_keys.append(key)
        return ndb.get_multi(list_of_keys)

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
        tokens = ','.join(Autocompleter.tokenize_autocomplete_simpler(phrase))
        document = search.Document(
            doc_id=item_id,
            fields=[
                search.TextField(name='tokens', value=tokens),
            ],
            rank=count,
            language='cs'
        )
        return document


    @staticmethod
    def tokenize_autocomplete(phrase):
        """
        Chops the phrase into substrings. This is the more complete version
        which includes things like 'rst' in phrase 'prsten'.
        """
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

    @staticmethod
    def tokenize_autocomplete_simpler(phrase):
        """
        Chops the phrase into substrings. This is the less complete version
        which only includes substrings from start of word.
        """
        a = []
        for word in phrase.split():
            for i in range(1, len(word) + 1):
                a.append(word[0:i])
        return a


class BookRecord(ndb.Model):
    author = ndb.StringProperty(indexed=False)
    title = ndb.StringProperty(indexed=False)
    year = ndb.IntegerProperty(indexed=False)
    count = ndb.IntegerProperty(indexed=False)

