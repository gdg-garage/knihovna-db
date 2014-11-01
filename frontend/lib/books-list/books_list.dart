library books_list;

import 'package:polymer/polymer.dart';
import '../models.dart';

@CustomTag('books-list')
class BooksList extends PolymerElement {
  @observable ObservableList books;

  BooksList.created() : super.created();

  void populateFromJson(Object jsonObject) {
    books = new ObservableList();
    assert(jsonObject is List);
    for (var map in jsonObject) {
      var book = new ListedBook.fromMap(map);
      books.add(book);
    }
  }
}