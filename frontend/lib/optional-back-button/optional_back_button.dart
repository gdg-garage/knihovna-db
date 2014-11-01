library optional_back_button;

import 'package:polymer/polymer.dart';
import '../models.dart';

@CustomTag('optional-back-button')
class OptionalBackButton extends PolymerElement {
  @published bool backButtonEnabled = false;

  OptionalBackButton.created() : super.created();

  void handleTap(_, __, ___) {
    if (backButtonEnabled) {
      fire("back-button-tapped");
    }
  }
}