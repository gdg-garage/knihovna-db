library books_list;

import 'package:polymer/polymer.dart';
import '../models.dart';

@CustomTag('books-list')
class BooksList extends PolymerElement {
  @observable ObservableList books;
  @observable ListedBook originalBook;

  BooksList.created() : super.created();

  void populateFromJson(var jsonObject) {
    var map = jsonObject as Map<String,Object>;
    assert(map['version'] == '0.0.1');
    originalBook = new ListedBook.fromMap(map['originalBook']);
    books = new ObservableList();
    for (var bookMap in map['suggestions']) {
      var book = new ListedBook.fromMap(bookMap);
      books.add(book);
    }
  }
}