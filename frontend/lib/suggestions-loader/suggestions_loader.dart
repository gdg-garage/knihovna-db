import 'package:polymer/polymer.dart';
import 'package:core_elements/core_ajax_dart.dart';
import 'dart:convert';

@CustomTag('suggestions-loader')
class SuggestionsLoader extends PolymerElement {
  CoreAjax _coreAjaxForResults;

  SuggestionsLoader.created() : super.created() {
    Polymer.onReady.then((_) {
      _coreAjaxForResults = $['ajax-results'];
      _coreAjaxForResults.onCoreResponse
        .listen(_showSuggestions);
    });
  }

  void startLoading(int itemId) {
    _sendAjaxRequest(itemId);
  }

  void _showSuggestions(_) {
    print("Suggestion loaded!");
    fire("suggestions-loaded", detail: _coreAjaxForResults.response);
  }

  _sendAjaxRequest(int itemId) {
    _coreAjaxForResults.params = JSON.encode({"item_id": itemId.toString()});
    _coreAjaxForResults.go();
  }
}

