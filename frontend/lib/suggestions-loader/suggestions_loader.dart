library suggestion_loader;

import 'package:polymer/polymer.dart';
import 'package:core_elements/core_ajax_dart.dart';
import 'package:paper_elements/paper_toast.dart';
import 'dart:convert';
import 'dart:async';

import '../models.dart';

@CustomTag('suggestions-loader')
class SuggestionsLoader extends PolymerElement {
  CoreAjax _coreAjaxForResults;
  String itemIds;

  @observable
  bool isLongerWait = false;
  @observable
  BookWithMetadata originalBook;
  @observable
  bool isLoaded = false;


  SuggestionsLoader.created() : super.created();

  domReady() {
    _coreAjaxForResults = $['ajax-results'];
    /* #if DEBUG */
    _coreAjaxForResults.url = '/packages/knihovna_frontend/suggestions-loader/'
        'mock_suggestion_results.json';
    /* #endif */

    _coreAjaxForResults.onCoreResponse
      .listen(_showSuggestions);
  }

  void startLoading(String itemIds) {
    this.itemIds = itemIds;
    isLongerWait = false;
    originalBook = BookWithMetadata.BLANK;
    isLoaded = false;
//    isLongerWait = true;
//    new Timer(const Duration(seconds: 2), () {
//      _sendAjaxRequest();
//    });
    _sendAjaxRequest();
  }

  static const DELAY_BETWEEN_RETRIES = const Duration(seconds: 5);
  static const int MAX_RETRIES = 100;

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
      if (!numberOfTries.containsKey(itemIds)) {
        originalBook = new BookWithMetadata.fromMap(
            _coreAjaxForResults.response['original_book']);
        numberOfTries[itemIds] = 0;
      }
      numberOfTries[itemIds]++;
      if (numberOfTries[itemIds] > MAX_RETRIES) {
        print("No more tries left.");
        // TODO: tell user we have failed
      } else {
        print("Will retry.");
        isLongerWait = true;
        new Timer(DELAY_BETWEEN_RETRIES, () {
          _sendAjaxRequest();
        });
      }
      return;
    }
    print("Suggestion loaded!");

    if (isLongerWait) {
      isLoaded = true;
      ($['loaded-toast'] as PaperToast).show();
    } else {
      fireSuggestionsLoaded(null, null, null);
    }
  }

  fireSuggestionsLoaded(_, __, ___) {
    fire("suggestions-loaded", detail: _coreAjaxForResults.response);
  }

  /// Sends ajax for the current [itemId].
  _sendAjaxRequest() {
    _coreAjaxForResults.params = JSON.encode({"q": itemIds});
    _coreAjaxForResults.go();
  }
}

