import 'package:polymer/polymer.dart';
import '../models.dart';

@CustomTag('books-list')
class BooksList extends PolymerElement {
  @observable ObservableList books;

  BooksList.created() : super.created();

  void populateFromJson(Object jsonObject) {
    books = new ObservableList();
    assert(jsonObject is List);
    for (var map in jsonObject) {
      var book = new ListedBook.fromMap(map);
      books.add(book);
      print(book); // TODO get rid of this
    }
    print(books);
  }
}

//class TestItem extends Observable {
//  final int id;
//  final String name;
//  final String details;
//  final int image;
//  @observable int value;
//  @observable int type;
//  @observable bool checked;
//
//  TestItem({this.id, this.name, this.details, this.image, this.value, this.type,
//           this.checked});
//}