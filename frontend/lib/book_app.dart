import 'package:polymer/polymer.dart';
import 'package:core_elements/core_animated_pages.dart';
import 'dart:html';

@CustomTag('book-app')
class BookApp extends PolymerElement {
  CoreAnimatedPages _animatedPages;

  BookApp.created() : super.created() {
    Polymer.onReady.then((_) {
      _animatedPages = $['animated-pages'];
    });

    // Copy contents from the LightDom.
    ($['tagline'] as ParagraphElement).text = querySelector(".tagline").text;
  }

  handleBookInput(a,b,c) {
    _animatedPages.selected = 1;
  }

}