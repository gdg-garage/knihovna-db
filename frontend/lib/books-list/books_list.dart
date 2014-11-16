library books_list;

import 'package:polymer/polymer.dart';
import 'package:paper_elements/paper_dialog.dart';
import '../models.dart';
import 'dart:html';

@CustomTag('books-list')
class BooksList extends PolymerElement {
  @observable ObservableList books;

  @observable BookWithMetadata originalBook;
  @observable SuggestedBook bookInInfoDialog = SuggestedBook.BLANK;
  @observable String bookInInfoDialogHref;

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

    int endMarginTop;
    if (books.length <= 30) {
      endMarginTop = 50;
    } else {
      // Polymer core-list is reusing 30 items all over again. If we didn't do
      // this, the end paragraph would be somewhere around item 30.
      endMarginTop = 100 * (books.length - 30) + 50;
    }
    $['end'].style.marginTop = '${endMarginTop}px';
  }

  void showAbout() {
    fire("show-about");
  }

  void showInfo(Event event, Object detail, Node sender) {
    String itemIds = (sender as Element).dataset['itemids'];

    // This is sub-ideal, but whatever.
    bookInInfoDialog = books
        .singleWhere((SuggestedBook book) => book.itemIds == itemIds);
    // TODO: get metadata

    String firstItemId = itemIds.split("|").first;
    bookInInfoDialogHref = "http://search.mlp.cz/cz/titul/$firstItemId/";

    ($['book-info'] as PaperDialog).opened = true;
  }
}