library books;

import 'package:observe/observe.dart';

class Book extends Observable {
  String author;
  String title;

  Book.fromMap(Map<String,Object> map) {
    author = map['author'];
    title = map['title'];
  }
}

class SuggestedBook extends Book {
  @observable bool selected = false;
  SuggestedBook.fromMap(Map<String, Object> map) : super.fromMap(map);
}