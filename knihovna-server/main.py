# coding=utf-8

import webapp2
from autocompleter import Autocompleter, BookRecord
import logging
import json


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        self.response.write('Hello, Světe!')


class AutocompleteJson(webapp2.RequestHandler):
    CURRENT_VERSION = 1

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        query = self.request.get('q')
        logging.info(u"Autocomplete search for '{}'".format(query))
        autocompleter = Autocompleter()
        results = autocompleter.get_results(query)
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
            'suggestions': json_results
        }
        self.response.write(json.dumps(json_object))


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/autocomplete/suggestions.json', AutocompleteJson)
], debug=True)