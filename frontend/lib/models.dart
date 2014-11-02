library books;

import 'package:observe/observe.dart';

class Book extends Observable {
  int itemId;
  String author;
  String title;
  // TODO: add year? (to distinguish)

  Book.fromMap(Map<String,Object> map) {
    author = map['author'];
    title = map['title'];
    itemId = map['itemId'];
  }

  toString() => "Book<$author//$title>";
}

class AutocompletedBook extends Book {
  @observable bool selected = false;
  AutocompletedBook.fromMap(Map<String, Object> map) : super.fromMap(map);
}

class ListedBook extends Book {
  String description;
  // TODO: add description, url, etc.

  ListedBook.fromMap(Map<String, Object> map) : super.fromMap(map) {
    description = map['description'];
  }
}