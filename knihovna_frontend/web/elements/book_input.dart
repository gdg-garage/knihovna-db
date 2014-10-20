import 'package:polymer/polymer.dart';
import 'dart:html';

@CustomTag('book-input')
class BookInput extends PolymerElement {

  BookInput.created() : super.created() {
  }

  void handleKeyDown(Event e, var detail, Node target) {
    int code = (e as KeyboardEvent).keyCode;
    switch (code) {
      case 40:
        print("Down!");
        e.preventDefault();
        break;
      case 38:
        print("Up!");
        e.preventDefault();
        break;
    }
  }
}

