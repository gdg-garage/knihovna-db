

import logging
import os
import codecs
from book_record import BookAnnotation, BookRecord
from google.appengine.api import app_identity
import third_party.cloudstorage as gcs
import third_party.unicodecsv as ucsv
from google.appengine.ext import deferred
from google.appengine.ext import ndb
from utils import is_dev_server

MAX_OBJECTS_PER_BATCH = 500


def _put_annotations_batch(annotation_data):
    try:
        annotation_objects = []
        qry = BookRecord.query(
            BookRecord.item_id_array.IN(annotation_data.keys())
        )
        keys = qry.fetch(MAX_OBJECTS_PER_BATCH, keys_only=True)
        for key in keys:
            first_item_id = key.string_id().split('|')[0]

            if first_item_id not in annotation_data:
                continue

            short_text = annotation_data[first_item_id][0]
            long_text = annotation_data[first_item_id][1]

            anno_key = ndb.Key(BookAnnotation, key.string_id())
            annotation = BookAnnotation(key=anno_key,
                                        short=short_text,
                                        long=long_text)
            annotation_objects.append(annotation)
        ndb.put_multi(annotation_objects)
        logging.info("{} annotations put into datastore"
                     .format(len(annotation_objects)))
    except Exception as e:
        logging.error(e)
        raise deferred.PermanentTaskFailure()


def update_annotations_from_csv(filename="anotace.csv"):
    logging.info("Starting to update from CSV")

    my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                              max_delay=5.0,
                                              backoff_factor=2,
                                              max_retry_period=15)
    gcs.set_default_retry_params(my_default_retry_params)
    # bucket_name = os.environ.get('BUCKET_NAME',
    #                              app_identity.get_default_gcs_bucket_name())
    bucket_name = "tisic-knih.appspot.com"
    bucket = '/' + bucket_name
    filename = bucket + '/' + filename
    try:
        if is_dev_server():
            gcs_file = open("anotace.csv")
        else:
            gcs_file = gcs.open(filename)
        # gcs_file.seek(1000)
        r = ucsv.reader(gcs_file, encoding='utf-8')
        r.next()  # Skip first line (header).
        annotation_data = {}

        for row_number, row in enumerate(r):
            if row_number % 10000 == 0:
                logging.info("Processing row number {} of CSV file. "
                             .format(row_number))
            item_id = row[0]
            short_text = row[1]
            long_text = row[2]
            annotation_data[item_id] = (short_text, long_text)
            if len(annotation_data) > MAX_OBJECTS_PER_BATCH:
                deferred.defer(_put_annotations_batch, annotation_data)
                annotation_data = {}

        deferred.defer(_put_annotations_batch, annotation_data)
        gcs_file.close()
    except Exception as e:
        logging.error(e)
        raise deferred.PermanentTaskFailure()
