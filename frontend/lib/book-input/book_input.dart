import 'package:polymer/polymer.dart';
import 'dart:html';
import 'package:paper_elements/paper_input.dart';
import 'dart:async';
import 'package:rate_limit/rate_limit.dart';
import 'book_suggestion_list.dart';
import 'package:core_elements/core_ajax_dart.dart';
import 'dart:convert';

@CustomTag('book-input')
class BookInput extends PolymerElement {
  StreamController<String> _newValue = new StreamController<String>();

  BookInput.created() : super.created() {
    // Wait for Polymer to initialize before searching $[] fields.
    Polymer.onReady.then((_) {
      _inputElement = $['searchbox'] as PaperInput;

      _suggestionList = $['suggestion-list'];

      _coreAjax = $['ajax'];
      _coreAjax.onCoreResponse
        .transform(new Debouncer(const Duration(milliseconds: 150)))
        .listen(_showNewSuggestions);

      _newValue.stream
      .transform(new Debouncer(const Duration(milliseconds: 150)))
      .listen(_sendAjaxRequest);
    });
  }

  BookSuggestionList _suggestionList;
  CoreAjax _coreAjax;
  PaperInput _inputElement;

  void handleKeyDown(Event e, var detail, Node target) {
    int code = (e as KeyboardEvent).keyCode;
    switch (code) {
      case KeyCode.DOWN:
        _suggestionList.moveDown();
        e.preventDefault();
        break;
      case KeyCode.UP:
        _suggestionList.moveUp();
        e.preventDefault();
        break;
      case KeyCode.ENTER:
        var book = _suggestionList.selectedBook;
        if (book != null) {
          fire("book-selected", detail: _suggestionList.selectedBook);
        } else {
          // Unfocus for the benefit of mobile users who don't see the
          // suggestions because of their software keyboard overlay.
          _inputElement.blur();
        }
        e.preventDefault();
        break;
    }
  }

  void handleChange(Event e, var detail, Node target) {
    _newValue.add(_inputElement.inputValue);  // Throttles through Debouncer.
  }

  _sendAjaxRequest(String value) {
    if (value.trim() == "") {
      _suggestionList.clear();
      return;
    }
    _coreAjax.params = JSON.encode({"q": value});
    _coreAjax.go();
    _suggestionList.isLoading = true;
  }

  void _showNewSuggestions(CustomEvent event) {
    _suggestionList.createSuggestionsFromJson(_coreAjax.response);
    _suggestionList.isLoading = false;
  }
}

