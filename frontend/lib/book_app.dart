import 'package:polymer/polymer.dart';
import 'package:core_elements/core_animated_pages.dart';
import 'dart:html';
import 'suggestions-loader/suggestions_loader.dart';
import 'books-list/books_list.dart';

@CustomTag('book-app')
class BookApp extends PolymerElement {
  static const String STATE_WELCOME = 'welcome';
  static const String STATE_WAIT = 'wait';
  static const String STATE_LIST = 'list';

  CoreAnimatedPages _animatedPages;
  SuggestionsLoader _suggestionsLoader;
  BooksList _booksList;

  BookApp.created() : super.created() {
    Polymer.onReady.then((_) {
      _animatedPages = $['animated-pages'];
      _suggestionsLoader = $['loader'];
      _booksList = $['list'];
    });

    // Copy contents from the LightDom.
    ($['tagline'] as ParagraphElement).text = querySelector(".tagline").text;
  }

  handleBookInput(_, var detail, __) {
    _switchTo(STATE_WAIT);  // Show the suggestions-loader state.
    _suggestionsLoader.startLoading(0);  // TODO: provide itemId here.
  }

  handleSuggestionsLoaded(_, var detail, __) {
    print("Showing the ${(detail as List).length} items.");
    _booksList.populateFromJson(detail);
    _switchTo(STATE_LIST);
  }

  void _switchTo(String state) {
    // We can use String here because the <core-animated-pages> element has
    // valueattr set to 'id'.
    _animatedPages.selected = state;
  }


}