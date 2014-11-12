library quotes_gadget;

import 'package:polymer/polymer.dart';
import 'dart:html';
import 'package:core_elements/core_animated_pages.dart';

@CustomTag('quotes-gadget')
class QuotesGadget extends PolymerElement {
  List<Quote> quotes = toObservable([]);

  QuotesGadget.created() : super.created();

  CoreAnimatedPages _animatedPages;

  domReady() {
    _animatedPages = $['animated-quote-pages'];

    var distributedItems = this.querySelectorAll(".item");
    if (distributedItems.length == 0) {
      throw new StateError("Cannot create quotes gadget when no inner nodes "
          "are present. Please include <item><quote>Something</quote>"
          "<author>Someone</author></item> for this to work.");
    }

    for (DivElement item in distributedItems) {
      quotes.add(new Quote(item.querySelector(".author").text,
                           item.querySelector(".text").text));
    }
  }

  showPrevious(_, __, ___) {
    _animatedPages.selectPrevious(true);
  }

  showNext(_, __, ___) {
    _animatedPages.selectNext(true);
  }
}

class Quote {
  final String author;
  final String text;

  Quote(this.author, this.text);
}