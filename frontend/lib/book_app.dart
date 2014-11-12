import 'package:polymer/polymer.dart';
import 'package:core_elements/core_animated_pages.dart';
import 'dart:html';
import 'book-input/book_input.dart';
import 'suggestions-loader/suggestions_loader.dart';
import 'books-list/books_list.dart';
import 'pushdown_automaton.dart';
import 'models.dart';

import 'package:route/client.dart';
import 'package:route/url_pattern.dart';
import 'dart:async';

@CustomTag('book-app')
class BookApp extends PolymerElement {
  State _welcome;

  PushdownAutomatonStateMachine<State> _machine;
  State get currentState => _machine.currentState;

  @observable
  bool backButtonEnabled = false;

  CoreAnimatedPages _animatedPages;
  BookInput _bookInput;
  SuggestionsLoader _suggestionsLoader;
  BooksList _booksList;

  Router _router;

  /* #if DEBUG *//*
  static const String BASE_PATH = "";
  *//* #else */
  static const String BASE_PATH = "";
  /* #endif */

  UrlPattern _welcomeUrl;
  UrlPattern _listUrl;
  UrlPattern _detailUrl;

  BookApp.created() : super.created() {
    _welcome = new State('welcome', BASE_PATH + '/');
    _welcomeUrl = new UrlPattern(BASE_PATH + r'/(index.html)?');
    _listUrl = new UrlPattern(BASE_PATH + r'/#([\d|]+)');
    _detailUrl = new UrlPattern(BASE_PATH + r'/#(\d+)/detail-([\d|]+)');

    _machine = new PushdownAutomatonStateMachine<State>(initialState: _welcome);

    // #if DEBUG
    print("Running in debug mode.");
    // #else
    print("Running in release mode.");
    // #endif
  }

  domReady() {
    _animatedPages = $['animated-pages'];
    _bookInput = $['book-input'];
    _suggestionsLoader = $['loader'];
    _booksList = $['list'];

    _router = new Router()
      ..addHandler(_welcomeUrl, routeToWelcome)
      ..addHandler(_listUrl, routeToLoaderOrList)
      ..addHandler(_detailUrl, routeToDetail);
    _router.listen();

    // This breaks in Safari and Firefox, currently.
    try {
      _router.gotoPath("${window.location.pathname}${window.location.hash}",
      "Something" /* TODO */);
    } catch (e) {
      print("Are you running Safari or Firefox by any chance?");
      window.console.error(e);
    }

    ($["app-name"] as DivElement).text = querySelector(".app-name").text;
    _copyFromLightDom("app-name");
    _copyFromLightDom("h1");
    _copyFromLightDom("tagline");
    _copyFromLightDom("below-input");
  }

  /// Copy contents from the LightDom. (Gets around Firefox/Safari not applying
  /// style inside elements.)
  void _copyFromLightDom(String className) {
    ($[className] as Element).text = querySelector(".$className").text;
  }

  handleBookInput(_, var detail, __) {
    print("Book selected: $detail");
    var book = detail as AutocompletedBook;
    _router.gotoPath(_listUrl.reverse(["${book.itemIds}"], useFragment: true),
                     book.title);
  }

  void routeToWelcome(String path) {
    _machine.states.clear();
    _machine.pushTo(_welcome);
    _bookInput.unselectAutocomplete();
    _showStatePage();
  }

  void routeToLoaderOrList(String path) {
    // TODO: find out if we already have this loaded, skip to LIST if so
    String itemIds = _listUrl.parse(path)[0];
    _suggestionsLoader.startLoading(itemIds);
    var wait = new WaitState(path);
    _machine.pushTo(wait);
    _showStatePage();
  }

  handleSuggestionsLoaded(_, var detail, __) {
    if (currentState is! WaitState) {
      print("Suggestions loaded, but we are already elsewhere.");
      return;
    }
    // Wait a little while before
    new Timer(const Duration(milliseconds: 200), () {
      _booksList.populateFromJson(detail);
      var list = new ListState(currentState.url);
      _machine.switchTo(list);
      _showStatePage();
    });
  }

  void routeToDetail(String path) {
    throw new UnimplementedError("Detail not yet implemented.");
  }

  void _showStatePage() {
    // We can use String here because the <core-animated-pages> element has
    // valueattr set to 'id'.
    _animatedPages.selected = currentState.name;
    backButtonEnabled = _machine.states.length > 1;
  }

  /// Called when the back button in the app is tapped.
  void goToParentState(_, __, ___) {
    assert(_machine.states.length > 1);
    _machine.pop();
    _router.gotoPath(currentState.url, currentState.name /*TODO*/);
  }
}

class State {
  final String name;
  final String url;
  const State(this.name, this.url);
}

class WaitState extends State {
  WaitState(String url) : super("wait", url);
}

class ListState extends State {
  ListState(String url) : super("list", url);
}

class DetailState extends State {
  DetailState(String url) : super("detail", url);
}