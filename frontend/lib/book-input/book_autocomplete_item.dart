import 'package:polymer/polymer.dart';
import '../models.dart';

@CustomTag('book-autocomplete-item')
class BookSuggestion extends PolymerElement {
  @published AutocompletedBook book;

  BookSuggestion.created() : super.created();

  void handleMouseOver(_, __, ___) {
    book.selected = true;
    fire("autocomplete-item-selected", detail: book);
  }

  void handleMouseOut(_, __, ___) {
    book.selected = false;
    fire("autocomplete-item-unselected", detail: book);
  }

  void handleTap(_, __, ___) {
    fire("book-selected", detail: book);
  }
}

