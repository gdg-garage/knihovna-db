# coding=utf-8

import webapp2
from autocompleter import Autocompleter, BookRecord
import logging
import json
from suggest import Suggester, SuggestionsRecord
from google.appengine.ext import ndb
import time


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        self.response.write('Hello, Světe!')


class AutocompleteJson(webapp2.RequestHandler):
    CURRENT_VERSION = 1

    def get(self):
        # logging.info("request start \n{}".format(time.clock() * 1000 % 1000))
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        query = self.request.get('q')
        logging.info(u"Autocomplete search for '{}'".format(query))
        autocompleter = Autocompleter()
        # logging.info("before autocompleter.get_results \n{}".format(time.clock() * 1000 % 1000))
        results = autocompleter.get_results(query)
        # logging.info("after autocompleter.get_results \n{}".format(time.clock() * 1000 % 1000))
        json_results = []
        for book in results:
            assert isinstance(book, BookRecord)
            suggestion_map = {'author': book.author, 'title': book.title,
                              'year': book.year, 'count': book.count,
                              'item_ids': book.key.string_id()}
            json_results.append(suggestion_map)

        json_object = {
            'query': query,
            'version': AutocompleteJson.CURRENT_VERSION,
            'status': 'completed',
            'suggestions': json_results
        }
        # logging.info("before json.dump \n{}".format(time.clock() * 1000 % 1000))
        self.response.write(json.dumps(json_object, indent=2))
        # logging.info("after json.dump \n{}".format(time.clock() * 1000 % 1000))


class QuerySuggestions(webapp2.RequestHandler):
    CURRENT_VERSION = 1

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        # TODO: find out if the request is auto-repeated or new
        #       if new, force suggester to create new job if necessary
        item_ids = self.request.get('q')
        suggester = Suggester()
        suggestions = suggester.suggest(item_ids)
        assert isinstance(suggestions, SuggestionsRecord)
        json_object = {
            'version': QuerySuggestions.CURRENT_VERSION,
            'item_ids': item_ids,
            'job_started': suggestions.job_started.isoformat()
        }
        original_book = suggestions.original_book.get()
        assert isinstance(original_book, BookRecord)
        json_object['original_book'] = {
            'author': original_book.author,
            'title': original_book.title,
            'year': original_book.year
        }
        if suggestions.completed:
            json_object['status'] = 'completed'
            json_object['suggestions'] = []
            book_records = ndb.get_multi(suggestions.books)
            assert len(book_records) == len(suggestions.books_prediction)
            for i in xrange(len(book_records)):
                book = book_records[i]
                assert isinstance(book, BookRecord)
                json_object['suggestions'].append({
                    'author': book.author,
                    'title': book.title,
                    'item_ids': book.key.string_id(),
                    'prediction': suggestions.books_prediction[i]
                })
        else:
            json_object['status'] = 'started'

        self.response.write(json.dumps(json_object, indent=2))


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/autocomplete/suggestions.json', AutocompleteJson),
    ('/query/', QuerySuggestions)
], debug=True)