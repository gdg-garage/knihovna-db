library books;

import 'package:observe/observe.dart';

class Book extends Observable {
  final String itemIds;
  final String author;
  final String title;
  final int year;

  Book(this.itemIds, this.author, this.title, this.year);

  Book.fromMap(Map<String,Object> map)
  : author = map['author'],
    title = map['title'],
    itemIds = map['item_ids'],
    year = map['year'];

  toString() => "Book<$author//$title>";
}

class AutocompletedBook extends Book {
  @observable bool selected = false;
  AutocompletedBook.fromMap(Map<String, Object> map) : super.fromMap(map);
}

class BookWithMetadata extends Book {
  final String description;
  // TODO: add description, url, etc.

  BookWithMetadata(String itemIds, String author, String title, int year,
                   String description)
  : description = description,
    super(itemIds, author, title, year);

  BookWithMetadata.fromMap(Map<String, Object> map)
  : description = map['description'],
    super.fromMap(map);

  static final BookWithMetadata BLANK = new BookWithMetadata("", "", "", 0, "");
}

class SuggestedBook extends Book {
  static const double PREDICTION_THRESHOLD = 0.03;

  final double prediction;
  bool get suggestionWorthy => prediction > PREDICTION_THRESHOLD;

  SuggestedBook.fromMap(Map<String, Object> map)
  : prediction = map['prediction'],
    super.fromMap(map);
}