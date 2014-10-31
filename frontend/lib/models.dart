library books;

import 'package:observe/observe.dart';

class Book extends Observable {
  String author;
  String title;
  // TODO: add year? (to distinguish)

  Book.fromMap(Map<String,Object> map) {
    author = map['author'];
    title = map['title'];
  }

  toString() => "Book<$author//$title>";
}

class SuggestedBook extends Book {
  @observable bool selected = false;
  SuggestedBook.fromMap(Map<String, Object> map) : super.fromMap(map);
}

class ListedBook extends Book {
  @observable int itemId;
  // TODO: add description, url, etc.
//  @observable int index;     // list index for this item
//  @observable bool selected; // selection state for this item

  ListedBook.fromMap(Map<String, Object> map) : super.fromMap(map) {
    itemId = map['itemId'];
  }
}