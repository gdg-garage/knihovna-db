import 'package:polymer/polymer.dart';
import 'package:core_elements/core_animated_pages.dart';
import 'dart:html';
import 'suggestions-loader/suggestions_loader.dart';
import 'books-list/books_list.dart';

import 'package:knihovna_frontend/pushdown_automaton.dart';

@CustomTag('book-app')
class BookApp extends PolymerElement {
  static const String STATE_WELCOME = 'welcome';
  static const String STATE_WAIT = 'wait';
  static const String STATE_LIST = 'list';

  PushdownAutomatonStateMachine<String> _stateMachine =
      new PushdownAutomatonStateMachine<String>(initialState: STATE_WELCOME);

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

    // On each state change, call the method that changes the page in the
    // <core-animated-pages> element.
    _stateMachine.onNewState.listen(_showStatePage);
  }

  handleBookInput(_, var detail, __) {
    _stateMachine.pushTo(STATE_WAIT);  // Pushes to new state with possibility
                                       // to go back.
    _suggestionsLoader.startLoading(0);  // TODO: provide itemId here.
  }

  handleSuggestionsLoaded(_, var detail, __) {
    print("Showing the ${(detail as List).length} items.");
    if (_stateMachine.currentState != STATE_WAIT) {
      print("Suggestions loaded, but we are already elsewhere.");
      return;
    }
    _booksList.populateFromJson(detail);
    _stateMachine.switchTo(STATE_LIST);
  }

  void _showStatePage(String state) {
    // We can use String here because the <core-animated-pages> element has
    // valueattr set to 'id'.
    _animatedPages.selected = state;
  }
}