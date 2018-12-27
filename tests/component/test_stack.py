from unittest.mock import Mock, call

import pytest
from gi.repository import Gtk

from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel, StackView, StackPresenter


# Tests for StackModel

def test_stack_model_initial_state():
    stack_model = StackModel()

    assert stack_model.visible_child_key is None
    assert stack_model.bn_visible_child_key.get() is None


def test_stack_model_add_child():
    stack_model = StackModel()
    child = object()
    cb0 = Mock()
    stack_model.on_child_added.connect(cb0, immediate=True)
    cb1 = Mock()
    stack_model.bn_visible_child_key.on_changed.connect(cb1, immediate=True)

    # Add child.
    stack_model.add_child(0, child)

    # Make sure the on_child_added event was fired with the correct arguments.
    cb0.assert_called_once_with(0, child)

    # Make sure adding a child to a stack without a visible child does not automatically make the new child the visible
    # child.
    assert stack_model.visible_child_key is None
    assert stack_model.bn_visible_child_key.get() is None
    cb1.assert_not_called()


def test_stack_model_add_child_with_preexisting_key():
    stack_model = StackModel()
    child0 = object()
    child1 = object()
    stack_model.add_child(0, child0)

    # Add a different child but with a key that already identifies an existing child.
    with pytest.raises(ValueError):
        stack_model.add_child(0, child1)


def test_stack_model_add_child_with_key_none():
    stack_model = StackModel()
    child = object()

    # Add a child with an identifying key of None
    with pytest.raises(ValueError):
        stack_model.add_child(None, child)


def test_stack_model_add_preexisting_child_with_different_key():
    stack_model = StackModel()
    child = object()
    stack_model.add_child(0, child)

    # Add child again but with a different key.
    with pytest.raises(ValueError):
        stack_model.add_child(1, child)


def test_stack_model_get_child_from_key():
    stack_model = StackModel()
    child0 = object()
    child1 = object()
    stack_model.add_child(0, child0)
    stack_model.add_child(1, child1)

    assert stack_model.get_child_from_key(0) == child0
    assert stack_model.get_child_from_key(1) == child1


def test_stack_model_get_child_from_key():
    stack_model = StackModel()
    child0 = object()
    child1 = object()
    stack_model.add_child(0, child0)
    stack_model.add_child(1, child1)

    assert stack_model.get_child_from_key(0) == child0
    assert stack_model.get_child_from_key(1) == child1


def test_stack_model_get_child_from_key_with_nonexistent_key():
    stack_model = StackModel()
    child0 = object()
    child1 = object()
    stack_model.add_child(0, child0)
    stack_model.add_child(1, child1)

    with pytest.raises(ValueError):
        stack_model.get_child_from_key(2)


def test_stack_model_get_child_from_key_with_none_key():
    stack_model = StackModel()
    child0 = object()
    child1 = object()
    stack_model.add_child(0, child0)
    stack_model.add_child(1, child1)

    assert stack_model.get_child_from_key(None) is None


def test_stack_model_set_visible_child_key():
    stack_model = StackModel()
    child = object()
    stack_model.add_child(0, child)
    cb = Mock()
    stack_model.bn_visible_child_key.on_changed.connect(cb, immediate=True)

    # Set the visible child.
    stack_model.visible_child_key = 0

    cb.assert_called_once_with()
    assert stack_model.visible_child_key == 0
    assert stack_model.bn_visible_child_key.get() == 0


def test_stack_model_set_visible_child_key_to_nonexistent_key():
    stack_model = StackModel()
    child = object()
    stack_model.add_child(0, child)

    # Set the visible child to a key that does not identify any child.
    with pytest.raises(ValueError):
        stack_model.visible_child_key = 1
    with pytest.raises(ValueError):
        stack_model.bn_visible_child_key.set(1)


def test_stack_model_set_visible_child_key_to_none():
    stack_model = StackModel()
    child = object()
    stack_model.add_child(0, child)
    stack_model.visible_child_key = 0
    cb = Mock()
    stack_model.bn_visible_child_key.on_changed.connect(cb, immediate=True)

    # Set the visible child to None, i.e. make current visible child 'invisible'.
    stack_model.visible_child_key = None

    cb.assert_called_once_with()
    assert stack_model.visible_child_key is None
    assert stack_model.bn_visible_child_key.get() is None


def test_stack_model_remove_child():
    stack_model = StackModel()
    child = object()
    stack_model.add_child(0, child)
    cb = Mock()
    stack_model.on_child_removed.connect(cb, immediate=True)

    # Remove child.
    stack_model.remove_child(child)
    cb.assert_called_once_with(0, child)


def test_stack_model_remove_child_on_already_removed_child():
    stack_model = StackModel()
    child = object()
    stack_model.add_child(0, child)
    stack_model.remove_child(child)
    cb = Mock()
    stack_model.on_child_removed.connect(cb, immediate=True)

    # Remove child again.
    with pytest.raises(ValueError):
        stack_model.remove_child(child)

    cb.assert_not_called()


def test_stack_model_remove_nonexistent_child():
    stack_model = StackModel()
    child0 = object()
    child1 = object()
    stack_model.add_child(0, child0)
    cb = Mock()
    stack_model.on_child_removed.connect(cb, immediate=True)

    # Remove nonexistent child.
    with pytest.raises(ValueError):
        stack_model.remove_child(child1)

    cb.assert_not_called()


def test_stack_model_remove_visible_child():
    stack_model = StackModel()
    child = object()
    stack_model.add_child(0, child)
    stack_model.visible_child_key = 0
    cb0_stack_model_visible_child = object()  # use a singleton placeholder value to denote that the variable is unset
    def cb0(*_):
        nonlocal cb0_stack_model_visible_child
        cb0_stack_model_visible_child = stack_model.visible_child_key
    stack_model.on_child_removed.connect(cb0, immediate=True)
    cb1 = Mock()
    stack_model.bn_visible_child_key.on_changed.connect(cb1, immediate=True)

    # Remove the visible child.
    stack_model.remove_child(child)

    cb1.assert_called_once_with()
    assert cb0_stack_model_visible_child is None
    assert stack_model.visible_child_key is None
    assert stack_model.bn_visible_child_key.get() is None


def test_stack_model_remove_child_when_another_child_is_visible():
    stack_model = StackModel()
    child0 = object()
    child1 = object()
    stack_model.add_child(0, child0)
    stack_model.add_child(1, child1)
    stack_model.visible_child_key = 1
    cb = Mock()
    stack_model.bn_visible_child_key.on_changed.connect(cb, immediate=True)

    # Remove the visible child.
    stack_model.remove_child(child0)

    assert stack_model.visible_child_key == 1
    assert stack_model.bn_visible_child_key.get() == 1
    cb.assert_not_called()


def test_stack_model_clear():
    stack_model = StackModel()
    children = {i: object() for i in range(3)}
    for k, v in children.items():
        stack_model.add_child(k, v)
    cb = Mock()
    stack_model.on_child_removed.connect(cb, immediate=True)

    # Clear the stack.
    stack_model.clear()

    # Assert that the on_child_removed event was fired for each child that was added to the stack earlier.
    cb.assert_has_calls([call(k, v) for k, v in children.items()])


def test_stack_model_clear_with_visible_child():
    stack_model = StackModel()
    children = {i: object() for i in range(3)}
    for k, v in children.items():
        stack_model.add_child(k, v)
    stack_model.visible_child_key = 0
    cb = Mock()
    stack_model.bn_visible_child_key.on_changed.connect(cb, immediate=True)

    # Clear the stack.
    stack_model.clear()

    cb.assert_called_once_with()
    assert stack_model.visible_child_key is None
    assert stack_model.bn_visible_child_key.get() is None


def test_stack_model_remove_child_after_clear():
    stack_model = StackModel()
    children = {i: object() for i in range(3)}
    for k, v in children.items():
        stack_model.add_child(k, v)
    stack_model.clear()

    # Remove a child from the cleared stack.
    with pytest.raises(ValueError):
        stack_model.remove_child(children[1])


def test_stack_model_add_child_after_clear():
    stack_model = StackModel()
    children = {i: object() for i in range(3)}
    for k, v in children.items():
        stack_model.add_child(k, v)
    stack_model.clear()

    # Add back a child that was on the stack before it was cleared.
    stack_model.add_child(1, children[1])

    # Same as before, but add it back with a different key.
    stack_model.add_child(0, children[2])


# Tests for StackView

class MySimpleView(GtkWidgetView[Gtk.Label]):
    def __init__(self):
        self.widget = Gtk.Label(label='Text')
        self.widget.show()


def test_stack_view_add_child():
    stack_view = StackView()
    child_view0 = MySimpleView()
    child_view1 = MySimpleView()

    # Add child_view0 to stack_view
    stack_view.add_child(child_view0)

    # Assert that child_view0's widget was actually added onto the stack widget.
    assert {child_view0.widget} == set(stack_view.widget.get_children())

    # Add child_view1 to stack_view.
    stack_view.add_child(child_view1)

    # Assert that both child_view0 and child_view1's widgets are children of the stack widget.
    assert {child_view0.widget, child_view1.widget} == set(stack_view.widget.get_children())


def test_stack_view_remove_child():
    stack_view = StackView()
    child_view0 = MySimpleView()
    child_view1 = MySimpleView()
    stack_view.add_child(child_view0)
    stack_view.add_child(child_view1)

    # Remove child_view1 from the stack.
    stack_view.remove_child(child_view1)

    # Assert that only child_view0's widget remains as a child of stack.
    assert {child_view0.widget} == set(stack_view.widget.get_children())

    # Remove child_view0 from the stack.
    stack_view.remove_child(child_view0)

    # Assert that stack has no children.
    assert set() == set(stack_view.widget.get_children())


def test_stack_view_clear():
    stack_view = StackView()
    child_view0 = MySimpleView()
    child_view1 = MySimpleView()
    stack_view.add_child(child_view0)
    stack_view.add_child(child_view1)

    # Clear the stack.
    stack_view.clear()

    # Assert that stack has no children.
    assert set() == set(stack_view.widget.get_children())


def test_stack_view_set_visible_child():
    stack_view = StackView()
    child_view0 = MySimpleView()
    child_view1 = MySimpleView()
    stack_view.add_child(child_view0)
    stack_view.add_child(child_view1)

    # Make child_view1 visible.
    stack_view.set_visible_child(child_view1)

    # Assert that child_view1's widget is the visible widget.
    assert stack_view.widget.get_visible_child() == child_view1.widget

    # Make child_view0 visible.
    stack_view.set_visible_child(child_view0)

    # Assert that child_view0's widget is the visible widget.
    assert stack_view.widget.get_visible_child() == child_view0.widget


def test_stack_view_set_visible_child_to_none():
    stack_view = StackView()
    child_view = MySimpleView()
    stack_view.add_child(child_view)

    # This should not raise an exception, but its behaviour is not specified.
    stack_view.set_visible_child(None)


# Tests for StackPresenter

# todo: This class is not useful, its uses should be replaced with a Mock object.
class MockStackView:
    LOG_ADD_CHILD = 'LOG_ADD_CHILD'
    LOG_REMOVE_CHILD = 'LOG_REMOVE_CHILD'
    LOG_CLEAR = 'LOG_CLEAR'
    LOG_SET_VISIBLE_CHILD = 'LOG_SET_VISIBLE_CHILD'

    def __init__(self):
        self.log = []

    def add_child(self, view):
        self.log.append((self.LOG_ADD_CHILD, view))

    def remove_child(self, view):
        self.log.append((self.LOG_REMOVE_CHILD, view))

    def clear(self):
        self.log.append(self.LOG_CLEAR)

    def set_visible_child(self, view):
        self.log.append((self.LOG_SET_VISIBLE_CHILD, view))


def test_stack_presenter_clears_view():
    stack_model = StackModel()
    mock_stack_view = MockStackView()
    stack_presenter = StackPresenter(stack_model, mock_stack_view)

    # Assert that the presenter first clears the view.
    assert mock_stack_view.log[0] == MockStackView.LOG_CLEAR


def test_stack_presenter_propagates_child_addition():
    stack_model = StackModel()
    mock_stack_view = MockStackView()
    stack_presenter = StackPresenter(stack_model, mock_stack_view)

    # Clear the logs first to ignore previous events.
    mock_stack_view.log = []

    # Mock children
    child0 = object()
    child1 = object()

    # Add child0
    stack_model.add_child(0, child0)
    assert mock_stack_view.log == [(MockStackView.LOG_ADD_CHILD, child0)]

    # Add child1
    stack_model.add_child(1, child1)
    assert mock_stack_view.log == [(MockStackView.LOG_ADD_CHILD, child0), (MockStackView.LOG_ADD_CHILD, child1)]


def test_stack_presenter_propagates_child_removal():
    stack_model = StackModel()
    mock_stack_view = MockStackView()
    stack_presenter = StackPresenter(stack_model, mock_stack_view)

    # Mock children
    child0 = object()
    child1 = object()

    stack_model.add_child(0, child0)
    stack_model.add_child(1, child1)

    # Clear the logs first to ignore the LOG_ADD_CHILD events.
    mock_stack_view.log = []

    # Remove child1
    stack_model.remove_child(child1)
    assert mock_stack_view.log == [(MockStackView.LOG_REMOVE_CHILD, child1)]

    # Remove child0
    stack_model.remove_child(child0)
    assert mock_stack_view.log == [(MockStackView.LOG_REMOVE_CHILD, child1), (MockStackView.LOG_REMOVE_CHILD, child0)]


def test_stack_presenter_adds_existing_model_children():
    stack_model = StackModel()

    # Mock children
    child0 = object()
    child1 = object()

    stack_model.add_child(0, child0)
    stack_model.add_child(1, child1)

    mock_stack_view = MockStackView()
    stack_presenter = StackPresenter(stack_model, mock_stack_view)

    # Assert that the existing children in stack_model are added to the view.
    assert set(mock_stack_view.log) > {(MockStackView.LOG_ADD_CHILD, child0), (MockStackView.LOG_ADD_CHILD, child1)}


def test_stack_presenter_propagates_visible_child():
    stack_model = StackModel()

    # Mock children
    child0 = object()
    child1 = object()

    stack_model.add_child(0, child0)
    stack_model.add_child(1, child1)

    mock_stack_view = MockStackView()
    stack_presenter = StackPresenter(stack_model, mock_stack_view)

    # Clear the logs first to ignore the LOG_ADD_CHILD events.
    mock_stack_view.log = []

    # Set the visible child key to 1
    stack_model.visible_child_key = 1

    assert mock_stack_view.log == [(MockStackView.LOG_SET_VISIBLE_CHILD, child1)]


def test_stack_presenter_syncs_visible_child():
    stack_model = StackModel()

    # Mock children
    child0 = object()
    child1 = object()

    stack_model.add_child(0, child0)
    stack_model.add_child(1, child1)

    stack_model.visible_child_key = 1

    # Attach the presenter to the view and the model after a visible child has already been set on the model.
    mock_stack_view = MockStackView()
    stack_presenter = StackPresenter(stack_model, mock_stack_view)

    assert (MockStackView.LOG_SET_VISIBLE_CHILD, child1) in mock_stack_view.log


def test_stack_presenter_destroy():
    stack_model = StackModel()

    # Mock children
    child0 = object()
    child1 = object()

    stack_model.add_child(0, child0)
    stack_model.add_child(1, child1)

    mock_stack_view = MockStackView()
    stack_presenter = StackPresenter(stack_model, mock_stack_view)

    # Clear the logs first to ignore the LOG_ADD_CHILD events.
    mock_stack_view.log = []

    # Destroy the presenter
    stack_presenter.destroy()

    # Make sure the view is cleared after the presenter is destroyed.
    mock_stack_view.log.remove(MockStackView.LOG_CLEAR)

    # Add a new child.
    child2 = object()
    stack_model.add_child(2, child2)

    # Assert that the presenter has not propagated this child addition since it is destroyed.
    assert mock_stack_view.log == []

    # Remove a child.
    stack_model.remove_child(child1)

    # Assert that the presenter has not propagated this child removal.
    assert mock_stack_view.log == []

    stack_model.visible_child_key = 2

    # Assert that the presenter has not propagated the changing of the visible child.
    assert mock_stack_view.log == []
