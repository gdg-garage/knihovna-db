import 'package:polymer/polymer.dart';
import 'package:core_elements/core_animated_pages.dart';
import 'package:paper_elements/paper_dialog.dart';
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
  UrlPattern _deprecatedListUrl;
//  UrlPattern _detailUrl;

  BookApp.created() : super.created() {
    _welcome = new State('welcome', BASE_PATH + '/');
    _welcomeUrl = new UrlPattern(BASE_PATH + r'/(index.html)?');
    _deprecatedListUrl = new UrlPattern(BASE_PATH + r'/#!id=(\d+\|[\d\|]+)');
    _listUrl = new UrlPattern(BASE_PATH + r'/#!id=([\d\-]+)');
//    _detailUrl = new UrlPattern(BASE_PATH + r'/#!id=(\d+)&detail-([\d|]+)');

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
      ..addHandler(_deprecatedListUrl, routeFromDeprecatedLoaderUrl)
      ..addHandler(_listUrl, routeToLoaderOrList);
      // ..addHandler(_detailUrl, routeToDetail);
    _router.listen();

    // This is needed to give the rest of the page time to domReady().
    // TODO: less hacky please
    new Timer(const Duration(milliseconds: 10), () {
      // This breaks in Safari and Firefox, currently.
      try {
        _router.handle("${window.location.pathname}${window.location.hash}");
      } catch (e) {
        print("Are you running Safari or Firefox by any chance?");
        window.console.error(e);
      }
    });

    document.querySelector("img#loader-img-unresolved").remove();
  }

  handleBookInput(_, var detail, __) {
    print("Book selected: $detail");
    var book = detail as AutocompletedBook;
    String itemIds = book.itemIds.replaceAll("|", "-");
    _router.gotoPath(_listUrl.reverse([itemIds], useFragment: true),
                     book.title);
  }

  void routeToWelcome(String path) {
    _machine.states.clear();
    _machine.pushTo(_welcome);
    _bookInput.unselectAutocomplete();
    _showStatePage();
  }

  void routeFromDeprecatedLoaderUrl(String path) {
    // #if DEBUG
    print("Arrived at deprecated url - $path");
    // #endif
    String itemIds = _deprecatedListUrl.parse(path)[0];
    itemIds = itemIds.replaceAll('|', '-');
    // TODO: remove this state from window.history
    _router.gotoPath(_listUrl.reverse([itemIds], useFragment: true),
                     "Tisíc knih");
  }

  void routeToLoaderOrList(String path) {
    // TODO: find out if we already have this loaded, skip to LIST if so
    String itemIds = _listUrl.parse(path)[0];
    itemIds = itemIds.replaceAll('-', '|');
    _suggestionsLoader.startLoading(itemIds);
    var wait = new WaitState(path);
    if (_machine.currentState is! WaitState &&
        _machine.currentState is! ListState) {
      _machine.pushTo(wait);
    } else {
      // Guard against two or more wait states on top of each other.
      _machine.switchTo(wait);
    }
    _showStatePage();
  }

  handleSuggestionsLoaded(_, var detail, __) {
    if (currentState is! WaitState) {
      print("Suggestions loaded, but we are already elsewhere.");
      return;
    }
    // Wait a little while before
    new Timer(const Duration(milliseconds: 400), () {
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
    // #if DEBUG
    print(_machine.states);
    // #endif
  }

  /// Called when the back button in the app is tapped.
  void goToParentState(_, __, ___) {
    assert(_machine.states.length > 1);
    _machine.pop();
    _router.gotoPath(currentState.url, currentState.name /*TODO*/);
  }

  void showAbout() {
    ($['about'] as PaperDialog).opened = true;
  }

  @observable
  String sharingUrlComponent = "";
  @observable
  String sharingTextComponent = "";
  @observable
  String sharingText = "";

  void showSharingDialog(_, var detail, __) {
    String url = window.location.href;
    sharingUrlComponent = Uri.encodeQueryComponent(url);
    sharingText = (detail as Map)['text'];
    sharingTextComponent = Uri.encodeQueryComponent(sharingText);
    ($['sharing-dialog'] as PaperDialog).opened = true;
  }
}

class State {
  final String name;
  final String url;
  const State(this.name, this.url);

  toString() => "State<$name>";
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