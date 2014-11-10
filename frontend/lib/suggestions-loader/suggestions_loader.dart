library suggestion_loader;

import 'package:polymer/polymer.dart';
import 'package:core_elements/core_ajax_dart.dart';
import 'dart:convert';
import 'dart:async';

import '../util.dart';

@CustomTag('suggestions-loader')
class SuggestionsLoader extends PolymerElement {
  CoreAjax _coreAjaxForResults;
  String itemIds;

  SuggestionsLoader.created() : super.created();

  domReady() {
    _coreAjaxForResults = $['ajax-results'];
    if (runningInDevelopment) {
      _coreAjaxForResults.url = '/frontend/suggestions-loader/'
        'mock_suggestion_results.json';
    }
    _coreAjaxForResults.onCoreResponse
      .listen(_showSuggestions);
  }

  void startLoading(String itemIds) {
    this.itemIds = itemIds;
    _sendAjaxRequest();
  }

  static const DELAY_BETWEEN_RETRIES = const Duration(seconds: 5);
  static const int MAX_RETIRES = 20;

  Map<String,int> numberOfTries = new Map<String,int>();

  void _showSuggestions(_) {
    if (_coreAjaxForResults.response == null) {
      // Most likely we resent a request right after this was called.
      print("Response not loaded.");
      return;  // TODO: maybe re-send?
    }
    String itemIds = _coreAjaxForResults.response['item_ids'];
    if (itemIds != this.itemIds) {
      print("Got result for itemIds that we don't care for anymore.");
      return;
    }
    if (_coreAjaxForResults.response['status'] != 'completed') {
      print("Job still in progress. Will retry.");
      numberOfTries[itemIds] = numberOfTries.putIfAbsent(itemIds, () => 1) + 1;
      if (numberOfTries[itemIds] > MAX_RETIRES) {
        print("No more tries left.");
        // TODO: tell user we have failed
      } else {
        print("Will retry.");
        new Timer(DELAY_BETWEEN_RETRIES, () {
          _sendAjaxRequest();
        });
      }
      return;
    }
    print("Suggestion loaded!");
    fire("suggestions-loaded", detail: _coreAjaxForResults.response);
  }

  /// Sends ajax for the current [itemId].
  _sendAjaxRequest() {
    _coreAjaxForResults.params = JSON.encode({"q": itemIds});
    _coreAjaxForResults.go();
  }
}

