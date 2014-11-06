import logging
from bigquery import BigQueryTable


class _ConsolidatedBooksData(object):
    def __init__(self, item_ids, author, title, year, count):
        self.item_ids = item_ids
        self.author = author
        self.title = title
        self.year = year
        self.count = count


def consolidate_books(table):
    assert isinstance(table, BigQueryTable)
    books = []
    ignore_rows = []
    for i in range(table.nrows):
        if i % 50 == 0:
            logging.info("Consolidating books: row {}/{}".format(
                i, table.nrows
            ))
        if i in ignore_rows:
            continue
        row = table.data[i]
        item_ids = [row[0]]
        author = row[1]
        title = row[2]
        years = [row[3]]
        counts = [int(row[4])]
        author_and_title = u"{}//{}".format(author, title)
        for j in range(i + 1, table.nrows):
            row2 = table.data[j]
            other_author_and_title = u"{}//{}".format(row2[1], row2[2])
            if author_and_title != other_author_and_title:
                continue
            ignore_rows.append(j)
            item_ids.append(row2[0])
            years.append(row2[3])
            counts.append(int(row2[4]))
        year = None
        for year_str in years:
            try:
                year_candidate = int(unicode(year_str))
                if not year or year_candidate > year:
                    year = year_candidate
            except:
                pass
        count = 0
        prev_count_str = ""
        counts.sort(reverse=True)
        for count_str in counts:
            count_str = unicode(count_str)
            if count_str == prev_count_str:
                continue  # Exactly the same counts are suspicious
            count += int(count_str)
            prev_count_str = count_str
        book = _ConsolidatedBooksData(
            item_ids='|'.join(item_ids),
            author=author,
            title=title,
            year=year,
            count=count
        )
        books.append(book)
        logging.info(u"Book '{}' consolidated into item_ids='{}'.".format(
            author_and_title, book.item_ids
        ))
    logging.info("Consolidating books: done ({} books from {} rows)".format(
        len(books), table.nrows
    ))
    return books