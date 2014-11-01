import 'package:polymer/polymer.dart';
import 'package:core_elements/core_animated_pages.dart';
import 'dart:html';
import 'suggestions-loader/suggestions_loader.dart';
import 'books-list/books_list.dart';

import 'package:route/client.dart';

@CustomTag('book-app')
class BookApp extends PolymerElement {
  static const State STATE_WELCOME = const State('welcome');
  static const State STATE_WAIT =
      const State('wait', parentState: STATE_WELCOME);
  static const State STATE_LIST =
      const State('list', parentState: STATE_WELCOME);
  static const State STATE_DETAIL =
      const State('detail', parentState: STATE_LIST);

  State state = STATE_WELCOME;

//  @ComputedProperty('stateMachine.states.length > 1')
//  bool get backButtonEnabled => readValue(#backButtonEnabled);
  @observable
  bool backButtonEnabled = false;

  CoreAnimatedPages _animatedPages;
  SuggestionsLoader _suggestionsLoader;
  BooksList _booksList;

  Router _router;

  static const BASE_PATH = "/frontend"; // XXX: hack to make this work in WebStorm

  final _homeUrl = new UrlPattern(BASE_PATH + r'/(index.html)?');
  final _listUrl = new UrlPattern(BASE_PATH + r'/#(\d+)');
  final _detailUrl = new UrlPattern(BASE_PATH + r'/#(\d+)/detail-(\d+)');

  BookApp.created() : super.created() {
    Polymer.onReady.then((_) {
      _animatedPages = $['animated-pages'];
      _suggestionsLoader = $['loader'];
      _booksList = $['list'];

      _router = new Router()
        ..addHandler(_homeUrl, showWelcome)
        ..addHandler(_listUrl, showLoaderOrList)
        ..addHandler(_detailUrl, showDetail);
      _router.listen();

      _router.gotoPath(window.location.pathname + window.location.hash,
          "Something" /* TODO */);
    });

    // Copy contents from the LightDom.
    ($['tagline'] as ParagraphElement).text = querySelector(".tagline").text;
  }

  handleBookInput(_, var detail, __) {
//    _router.gotoUrl(_listUrl, ["egeg" /* TODO */], "Hledám" /* TODO */);
    _router.gotoPath(_listUrl.reverse(["1234"], useFragment: true), "Hledám" /* TODO */);
  }

  void showLoaderOrList(String path) {
    // TODO: find out if we already have this loaded, skip to LIST if so
    int itemId = int.parse(_listUrl.parse(path)[0]);
    _suggestionsLoader.startLoading(itemId);
    state = STATE_WAIT;
    _showStatePage();
  }

  handleSuggestionsLoaded(_, var detail, __) {
    if (state != STATE_WAIT) {
      print("Suggestions loaded, but we are already elsewhere.");
      return;
    }
    _booksList.populateFromJson(detail);
    state = STATE_LIST;
    _showStatePage();
  }

  void _showStatePage() {
    // We can use String here because the <core-animated-pages> element has
    // valueattr set to 'id'.
    _animatedPages.selected = state.name;
    backButtonEnabled = state.parentState != null;
    print(backButtonEnabled);
  }

  void showWelcome(String path) {
    state = STATE_WELCOME;
    _showStatePage();
  }

  void showDetail(String path) {
    throw new UnimplementedError("Detail not yet implemented.");
  }

  void goToParentState(_, __, ___) {
    assert(state.parentState != null);
    state = state.parentState;
    _showStatePage();
  }
}

class State {
  final String name;
  final State parentState;
  const State(this.name, {this.parentState});
}