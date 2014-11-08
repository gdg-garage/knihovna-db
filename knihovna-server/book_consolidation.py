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
            # Construct consolidated item_ids (e.g. '23423|234235|314')
            item_ids_candidate = "{}|{}".format(item_ids, row[0])
            if len(item_ids_candidate) > 500:
                logging.warning("Consolidated key '{}' would be too long, "
                                "staying with the original key '{}'."
                                .format(item_ids_candidate, item_ids))
            else:
                item_ids = item_ids_candidate
            consolidated_books[book_hash] = (first_index, item_ids)
    logging.info("Consolidating books: done ({} books from {} rows)".format(
        len(consolidated_books), len(data)
    ))
    return consolidated_books