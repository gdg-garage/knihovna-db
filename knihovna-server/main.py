# coding=utf-8

import sys
import os
import logging
import urllib
from book_record import BookAnnotation

sys.path.append(os.path.join(os.path.dirname(__file__), "third_party"))

import webapp2
from autocompleter import Autocompleter, BookRecord
import json
from suggest import Suggester, SuggestionsRecord
from google.appengine.ext import ndb

from jinja import render_txt, render_html


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
            if book is None:
                logging.warning(u"Autocompleter result for '{}' returned None."
                                .format(query))
                continue
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
        item_ids = item_ids.replace('-', '|')
        suggester = Suggester()
        suggestions_json = suggester.get_json(item_ids)
        self.response.write(suggestions_json)


def get_jinja_template_values(suggestions):
    assert isinstance(suggestions, SuggestionsRecord)
    original_book = suggestions.original_book.get()
    book_records = ndb.get_multi(suggestions.books)
    suggestions = []
    for i, book in enumerate(book_records):
        url = u"http://search.mlp.cz/cz/titul/{}/".format(
            book.key.string_id().split('|')[0]
        )
        suggestions.append((
            i + 1, book.title, book.author, url
        ))
    values = {
        "originalBookName": original_book.title,
        "originalBookAuthor": original_book.author,
        "suggestions": suggestions
    }
    return values


class DownloadHandler(webapp2.RequestHandler):
    def get(self, item_ids, extension):
        assert extension == "txt"
        key = ndb.Key(SuggestionsRecord, item_ids)
        suggestions = key.get()
        if not suggestions or not suggestions.completed:
            self.error(404)
            self.response.out.write(u'Tato stránka neexistuje.')
            return
        values = get_jinja_template_values(suggestions)
        render_txt(self, "download.txt", values)


class RootHandler(webapp2.RequestHandler):
    def get(self):
        fragment = self.request.get('_escaped_fragment_')
        if not fragment:
            with open(os.path.join(os.path.dirname(__file__), "templates/index.html"), "r") as f:
                while True:
                    output = f.read()
                    if output == "":
                        break
                    self.response.write(output)
            return
        item_ids = None
        fragment = urllib.unquote(fragment)
        if not '=' in fragment:
            fragment = urllib.unquote(fragment)
            if not '=' in fragment:
                self.error(400)
                self.response.out.write(u"Bad request")
                return
        item_ids = fragment.split('=')[1]
        item_ids = item_ids.replace('-', '|')
        key = ndb.Key(SuggestionsRecord, item_ids)
        suggestions = key.get()
        if not suggestions or not suggestions.completed:
            self.redirect('/')
            return
        values = get_jinja_template_values(suggestions)
        # This is hacky. Should encode/decode path after hash bang?
        values["url"] = self.request.url.replace("?_escaped_fragment_=", "#!")
        # TODO: add the following when whe know that the book has image @ mlp.cz
        # first_id_string = "{:010d}".format(int(item_ids.split("|")[0]))
        # values["img"] = "http://web2.mlp.cz/koweb/{}/{}/{}/{}/Small.{}.jpg"\
        #     .format(
        #         first_id_string[0:2],
        #         first_id_string[2:4],
        #         first_id_string[4:6],
        #         first_id_string[6:8],
        #         first_id_string[8:],
        #     )
        render_html(self, "crawler.html", "", "", template_values=values)


class AnnotationHandler(webapp2.RequestHandler):
    CURRENT_VERSION = 1

    def _no_annotation(self, item_ids):
        self.response.write(json.dumps({
               'version': AnnotationHandler.CURRENT_VERSION,
               'item_ids': item_ids,
               'short': u"K této knize bohužel nemáme anotaci. :(",
               'long': ""
        }, indent=2))

    def get(self):
        item_ids = self.request.get('q')
        item_ids = item_ids.replace('-', '|')
        # TODO: fast check
        if item_ids == "":
            self._no_annotation(item_ids)
            return
        key = ndb.Key(BookAnnotation, item_ids)
        annotation = key.get()
        if not annotation:
            self._no_annotation(item_ids)
            return
        assert isinstance(annotation, BookAnnotation)
        json_object = {
            'version': AnnotationHandler.CURRENT_VERSION,
            'item_ids': item_ids,
            'short': annotation.short,
            'long': annotation.long
        }
        self.response.write(json.dumps(json_object, indent=2))


application = webapp2.WSGIApplication([
    ('/autocomplete/suggestions.json', AutocompleteJson),
    ('/query/', QuerySuggestions),
    ('/annotation/', AnnotationHandler),
    ('/download/([0-9|\-]+).(txt)', DownloadHandler),
    ('/', RootHandler)
], debug=True)