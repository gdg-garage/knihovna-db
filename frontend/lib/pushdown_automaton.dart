library pushdown_automaton;

import "dart:collection";
import 'dart:async';

/// Implements http://gameprogrammingpatterns.com/state.html#pushdown-automata
class PushdownAutomatonStateMachine<T> {
  final Queue<T> _states = new Queue<T>();
  final StreamController<T> _newStateStreamController =
      new StreamController<T>();

  T get currentState => _states.last;
  Stream<T> onNewState;

  PushdownAutomatonStateMachine({T initialState}) {
    onNewState = _newStateStreamController.stream;

    if (initialState != null) _states.add(initialState);
  }

  void switchTo(T state) {
    _states.removeLast();
    _states.addLast(state);
    _notifyState();
  }

  void pushTo(T state) {
    _states.addLast(state);
    _notifyState();
  }

  T pop() {
    T poppedState = _states.removeLast();
    _notifyState();
    return poppedState;
  }

  void _notifyState() {
    _newStateStreamController.add(_states.last);
  }
}