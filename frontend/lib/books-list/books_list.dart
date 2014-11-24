library books_list;

import 'package:polymer/polymer.dart';
import 'package:paper_elements/paper_dialog.dart';
import '../models.dart';
import 'dart:html';
import 'dart:js' as js;
import 'dart:async';

@CustomTag('books-list')
class BooksList extends PolymerElement {
  @observable ObservableList books;

  @observable BookWithMetadata originalBook;
  @observable SuggestedBook bookInInfoDialog = SuggestedBook.BLANK;
  @observable String bookInInfoDialogHref;

  PaperDialog _bookInfoDialog;

  BooksList.created() : super.created();

  void populateFromJson(var jsonObject) {
    var map = jsonObject as Map<String,Object>;
    assert(map['version'] == 1);
    assert(map['status'] == 'completed');
    map['original_book']['item_ids'] = map['item_ids'];  // Fix json.
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

    _bookInfoDialog = $['book-info'];

    // #if DEBUG
    print("${books.length} suggestions loaded");
    // #endif
  }

  void showAbout() {
    fire("show-about");
  }

  void showInfo(Event event, Object detail, Node sender) {
    String itemIds = (sender as Element).dataset['itemids'];

    // This is not ideal, but whatever.
    bookInInfoDialog = books
        .singleWhere((SuggestedBook book) => book.itemIds == itemIds);

    String firstItemId = itemIds.split("|").first;
    bookInInfoDialogHref = "http://search.mlp.cz/cz/titul/$firstItemId/";

    _bookInfoDialog.opened = true;
  }

  void showSharingDialog() {
    fire("show-sharing", detail: {
      "text": "${books.length} doporučení pro čtenáře knížky "
              "${originalBook.title}"
    });
  }

  void handleBookInfoContentResize() {
    var overlayEl = _bookInfoDialog.shadowRoot.querySelector("#overlay");
    var overlay = new js.JsObject.fromBrowserObject(overlayEl);
    // Wait for overlay to "size up" (= transform) before resizing it.
    new Timer(const Duration(milliseconds: 200), () {
      // #if DEBUG
      print("Resizing the overlay");
      // #endif

      overlay.callMethod('resizeHandler', []);
    });
  }
}