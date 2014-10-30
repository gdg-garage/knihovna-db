import 'package:polymer/polymer.dart';
import '../models.dart';

// TODO: use <core-list> here: https://www.polymer-project.org/docs/elements/core-elements.html#core-list
// TODO: also: core-selector

@CustomTag('book-suggestion-list')
class BookSuggestionList extends PolymerElement {
  @observable List<SuggestedBook> suggestions = toObservable(<SuggestedBook>[]);
  int _selected = -1;

  int get selected => _selected;

  @published
  bool get isLoading => readValue(#isLoading, () => false);
  set isLoading(bool newValue) => writeValue(#isLoading, newValue);

  BookSuggestionList.created() : super.created() {
  }

  void moveUp() {
    _changeSelected(_selected, _selected - 1);
  }

  void moveDown() {
    _changeSelected(_selected, _selected + 1);
  }

  void _changeSelected(int oldValue, int newValue) {
    _changeSelectionByIndex(oldValue, false);
    if (newValue >= suggestions.length) newValue = -1;
    if (newValue < -1) newValue = suggestions.length - 1;
    _selected = newValue;
    _changeSelectionByIndex(_selected, true);
  }

  void _changeSelectionByIndex(int index, bool value) {
    if (index >= 0 && index < suggestions.length) {
      suggestions[index].selected = value;
    }
  }

  void clear() {
    suggestions.clear();
    _selected = -1;
  }

  void createSuggestionsFromJson(var jsonObject) {
    // TODO: reset selection (but only if currently selected book != selected book in new collection)
    suggestions.clear();
    for (var map in (jsonObject as List)) {
      suggestions.add(new SuggestedBook.fromMap(map));
    }
  }
}

