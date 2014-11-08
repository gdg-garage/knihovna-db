# coding=utf-8
import logging
from book_record import BookRecord

from unidecode import unidecode
from google.appengine.api import search
from google.appengine.ext import ndb
import re
import time

class Autocompleter(object):
    def __init__(self):
        self.index = search.Index(name='book_autocomplete')

    SANITIZE_PATTERN = re.compile("[^a-zA-Z_0-9 ]")

    def get_results(self, query):
        # logging.info("get_results start \n{}".format(time.clock() * 1000 % 1000))
        query_ascii = unidecode(query)
        query_ascii = Autocompleter.SANITIZE_PATTERN.sub("", query_ascii)

        logging.info(u"Autocomplete search for '{}' sanitized to '{}'.".format(
            query, query_ascii
        ))

        if not query_ascii:
            return []

        # logging.info("before index search \n{}".format(time.clock() * 1000 % 1000))
        results = self.index.search(
            query=search.Query('tokens:({})'.format(query_ascii),
                options=search.QueryOptions(limit=5,
                                            ids_only=True)
            )
        )
        # logging.info("after index search \n{}".format(time.clock() * 1000 % 1000))
        logging.info("Got {} results.".format(len(results.results)))
        assert(isinstance(results, search.SearchResults))
        list_of_keys = []
        for search_result in results.results:
            assert(isinstance(search_result, search.ScoredDocument))
            key = ndb.Key('BookRecord', search_result.doc_id)
            list_of_keys.append(key)
        # logging.info("get_multi start \n{}".format(time.clock() * 1000 % 1000))
        return ndb.get_multi(list_of_keys)

    def add(self, item_id, author, title, year, count):
        document, record = Autocompleter.create_instances_to_be_saved(
            item_id, author, title, year, count
        )
        self.index.put(document)
        record.put()

    @staticmethod
    def create_instances_to_be_saved(item_ids, author, title, year, count):
        """
        A method that returns saveable objects without actually saving them.
        This allows batching saves.
        :param item_ids: String with unique item ids.
        :param author:
        :param title:
        :param year:
        :param count: Count. Will be forced to an integer if it isn't already.
        :return: a tuple of document (Search API) and record (NDB)
        """
        document = Autocompleter._create_document(item_ids, author, title,
                                                  count)
        record = Autocompleter._create_record(item_ids, author, title,
                                              year, count)
        return document, record


    @staticmethod
    def _create_record(item_ids, author, title, year, count):
        key = ndb.Key(BookRecord, item_ids)
        item_id_array = item_ids.split("|")
        datastore_record = BookRecord(
            key=key,
            item_id_array=item_id_array,
            author=author,
            title=title,
            year=year,
            count=count
        )
        return datastore_record


    @staticmethod
    def _create_document(item_ids, author, title, count):
        author_ascii = unidecode(author)
        title_ascii = unidecode(title)
        phrase = "{} {}".format(author_ascii, title_ascii)
        tokens = ','.join(Autocompleter.tokenize_autocomplete_simpler(phrase))
        document = search.Document(
            doc_id=item_ids,
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

    def delete_all(self):
        # looping because get_range by default returns up to 100 documents at a time
        while True:
            # Get a list of documents populating only the doc_id field and extract the ids.
            document_ids = [document.doc_id
                            for document in self.index.get_range(ids_only=True)]
            if not document_ids:
                break
            # Delete the documents for the given ids from the Index.
            self.index.delete(document_ids)
        logging.info("Whole index deleted")
