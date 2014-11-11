library books_list;

import 'package:polymer/polymer.dart';
import '../models.dart';

@CustomTag('books-list')
class BooksList extends PolymerElement {
  @observable ObservableList books;
  @observable BookWithMetadata originalBook;

  BooksList.created() : super.created();

  void populateFromJson(var jsonObject) {
    var map = jsonObject as Map<String,Object>;
    assert(map['version'] == 1);
    assert(map['status'] == 'completed');
    originalBook = new BookWithMetadata.fromMap(map['original_book']);
    books = new ObservableList();
    for (var bookMap in map['suggestions']) {
      var book = new SuggestedBook.fromMap(bookMap);
      if (book.suggestionWorthy) {
        books.add(book);
      }
    }
  }
}