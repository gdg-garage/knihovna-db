import logging
from bigquery import BigQueryTable


class _ConsolidatedBooksData(object):
    def __init__(self, item_ids, author, title, year, count):
        self.item_ids = item_ids
        self.author = author
        self.title = title
        self.year = year
        self.count = count


def consolidate_books(data):
    assert isinstance(data, list)
    # saves 'author/title hash': (first_index, 'item_ids')
    consolidated_books = {}
    for i, row in enumerate(data):
        if i % 10000 == 0:
            logging.info("Consolidating books: hash row {}/{}".format(
                i, len(data)
            ))
        book_hash = hash(u"{}//{}".format(
            row[1], # author
            row[2]  # title
        ))
        if not book_hash in consolidated_books:
            consolidated_books[book_hash] = (
                i,
                row[0],  # item_id
            )
        else:
            first_index, item_ids = consolidated_books[book_hash]
            item_ids = "{}|{}".format(item_ids, row[0])
            # truncate (key cannot be too long)
            item_ids = (item_ids[:500]) if len(item_ids) > 500 else item_ids
            consolidated_books[book_hash] = (first_index, item_ids)
    logging.info("Consolidating books: done ({} books from {} rows)".format(
        len(consolidated_books), len(data)
    ))
    return consolidated_books