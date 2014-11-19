import 'package:polymer/polymer.dart';
import '../models.dart';

// TODO: also: core-selector

@CustomTag('book-autocomplete-list')
class BookSuggestionList extends PolymerElement {
  @observable List<AutocompletedBook> suggestions =
      toObservable(<AutocompletedBook>[]);
  int _selected = -1;

  AutocompletedBook get selectedBook {
    if (_selected == -1) return null;
    return suggestions[_selected];
  }

  @published
  bool get isLoading => readValue(#isLoading, () => false);
  set isLoading(bool newValue) => writeValue(#isLoading, newValue);

  @observable
  bool inputEmpty = true;

  BookSuggestionList.created() : super.created();

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

  void unselect() {
    _selected = -1;
    _updateSelectedPropertiesFromIndex();
  }

  void createSuggestionsFromJson(var jsonObject) {
    suggestions.clear();
    // TODO: Unselect only if currently selected book != selected book in
    // new collection.
    _selected = -1;
    assert(jsonObject is Map);
    assert(jsonObject['status'] == 'completed');
    assert(jsonObject['version'] == 1);
    List jsonSuggestions = jsonObject['suggestions'];
    for (var map in jsonSuggestions) {
      suggestions.add(new AutocompletedBook.fromMap(map));
    }
  }

  void handleDirectSelection(_, var detail, __) {
    assert(detail != null && detail is AutocompletedBook);
    _selected = suggestions.indexOf(detail);
    _updateSelectedPropertiesFromIndex();
  }

  void handleDirectUnselection(_, var detail, __) {
    _selected = -1;
    _updateSelectedPropertiesFromIndex();
  }

  void _updateSelectedPropertiesFromIndex() {
    for (int i = 0; i < suggestions.length; i++) {
      suggestions[i].selected = i == _selected;
    }
  }
}

