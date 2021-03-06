library book_input;

import 'package:polymer/polymer.dart';
import 'dart:html';
import 'package:paper_elements/paper_input.dart';
import 'package:paper_elements/paper_toast.dart';
import 'dart:async';
import 'package:rate_limit/rate_limit.dart';
import 'book_autocomplete_list.dart';
import 'package:core_elements/core_ajax_dart.dart';
import 'dart:convert';

@CustomTag('book-input')
class BookInput extends PolymerElement {
  StreamController<String> _newValue = new StreamController<String>();

  BookInput.created() : super.created();

  domReady() {
    _inputElement = $['searchbox'] as PaperInput;
    _inputElement.scrollIntoView(ScrollAlignment.TOP);

    _suggestionList = $['suggestion-list'];

    _enterToastElement = $['enter-toast'];

    _coreAjax = $['ajax'];
    /* #if DEBUG */
    _coreAjax.url = '/packages/knihovna_frontend/book-input/mock_response.json';
    /* #endif */

    _coreAjax.onCoreResponse
      .listen(_showNewSuggestions);

    _newValue.stream
      // ~ 33 words per minute = 400ms between characters
      .transform(new Debouncer(const Duration(milliseconds: 500)))
      .listen(_sendAjaxRequest);

    _hintElement = $['napis'] as ImageElement;
    _hintTimer = new Timer(const Duration(seconds: 10), () {
      showInputHint();
    });
  }

  BookSuggestionList _suggestionList;
  CoreAjax _coreAjax;
  PaperInput _inputElement;
  PaperToast _enterToastElement;
  ImageElement _hintElement;
  Timer _hintTimer;

  void showInputHint() {
    _hintElement.attributes.remove("hidden");
    _inputElement.focus();
  }

  void hideInputHint() {
    _hintElement.attributes["hidden"] = "";
  }

  void cancelHintTimer() {
    _hintTimer.cancel();
  }

  void selectUp(Event e, var detail, Node target) {
    _suggestionList.moveUp();
  }

  void selectDown(Event e, var detail, Node target) {
    _suggestionList.moveDown();
  }

  void unselectAutocomplete() {
    _suggestionList.unselect();
  }

  void handleEnterPressed(Event e, var detail, Node target) {
    var book = _suggestionList.selectedBook;
    if (book != null) {
      fire("book-selected", detail: _suggestionList.selectedBook);
    } else {
      // Unfocus for the benefit of mobile users who don't see the
      // suggestions because of their software keyboard overlay.
      _inputElement.blur();
      _enterToastElement.show();
    }
  }

  void handleChange(Event e, var detail, Node target) {
    _hintTimer.cancel();
    hideInputHint();
    _newValue.add(_inputElement.inputValue);  // Throttles through Debouncer.
  }

  _sendAjaxRequest(String value) {
    if (value.trim() == "") {
      _suggestionList.clear();
      _suggestionList.inputEmpty = true;
      return;
    }
    _coreAjax.params = JSON.encode({"q": value});
    _coreAjax.go();
    _suggestionList.isLoading = true;
    _suggestionList.inputEmpty = false;
  }

  void _showNewSuggestions(CustomEvent event) {
    if (_coreAjax.response != null) {
      _suggestionList.createSuggestionsFromJson(_coreAjax.response);
    }
    _suggestionList.isLoading = false;
  }
}

