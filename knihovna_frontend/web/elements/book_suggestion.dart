import 'package:polymer/polymer.dart';
import '../models.dart';

@CustomTag('book-suggestion')
class BookSuggestion extends PolymerElement {
  @published
  SuggestedBook get book => readValue(#book);
  set book(SuggestedBook newValue) => writeValue(#book, newValue);

  BookSuggestion.created() : super.created() {
  }
}

