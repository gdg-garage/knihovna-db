library book_annotation;

import 'package:polymer/polymer.dart';
import 'dart:html';
import 'dart:async';
import 'package:core_elements/core_ajax_dart.dart';
import 'dart:convert';

@CustomTag('book-annotation')
class BookAnnotation extends PolymerElement {
  @published
  String itemIds;

  @observable
  String short = " ";
  @observable
  String long = "";

  CoreAjax _ajax;

  domReady() {
    _ajax = $['book-anno-ajax'];
    // #if DEBUG
    _ajax.url = "/packages/knihovna_frontend/book-annotation/mock_annotation.json";
    // #endif
    _ajax.onCoreResponse.listen(_ajaxHandler);
  }

  itemIdsChanged(_) {
    if (_ajax == null) return;
    _ajax.params = JSON.encode({"q": itemIds});
    _ajax.go();
    short = "Nahrávám anotaci knížky...";
    long = "";
  }

  _ajaxHandler(_) {
    short = _ajax.response['short'];
    long = _ajax.response['long'];
    fire('book-annotation-loaded');
  }

  BookAnnotation.created() : super.created();
}