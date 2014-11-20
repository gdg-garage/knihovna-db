# coding=utf-8
from google.appengine.ext import ndb


class BookRecord(ndb.Model):
    # item_ids are stored in key like so '1234|345345|345254352'
    item_id_array = ndb.StringProperty(repeated=True)
    author = ndb.StringProperty(indexed=False)
    title = ndb.StringProperty(indexed=False)
    year = ndb.IntegerProperty(indexed=False)
    count = ndb.IntegerProperty(indexed=False)


class BookAnnotation(ndb.Model):
    # item_ids are stored in key like so '1234|345345|345254352'
    short = ndb.StringProperty(indexed=False)
    long = ndb.TextProperty(indexed=False)