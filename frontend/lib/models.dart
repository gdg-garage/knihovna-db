library books;

import 'package:observe/observe.dart';

class Book extends Observable {
  final String itemIds;
  final String author;
  final String title;
  final int year;

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

class ListedBook extends Book {
  final String description;
  // TODO: add description, url, etc.

  ListedBook.fromMap(Map<String, Object> map)
  : description = map['description'],
    super.fromMap(map);
}