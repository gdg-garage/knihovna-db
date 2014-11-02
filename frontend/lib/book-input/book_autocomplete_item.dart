import 'package:polymer/polymer.dart';
import '../models.dart';

@CustomTag('book-autocomplete-item')
class BookSuggestion extends PolymerElement {
  @published SuggestedBook book;

  BookSuggestion.created() : super.created() {
  }
}

