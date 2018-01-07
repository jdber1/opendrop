from mock import Mock
from pytest import raises

from opendrop.mvp.Application import VPRegistry


def test_stub():
    pass


class TestVPRegistry:
    def setup(self):
        self.vp_registry = VPRegistry()

    def test_new_record(self):
        self.vp_registry.new_record(view=Mock(), presenter=Mock(), model=Mock(), attached_to_parent=True)

    def test_get_record_by_view(self):
        my_view = Mock()

        record = self.vp_registry.new_record(view=my_view, presenter=Mock())

        test_record = self.vp_registry.get_record_by_view(my_view)

        assert test_record == record

        my_child_view = Mock()

        child_record = record.new_record(view=my_child_view, presenter=Mock())

        test_record = self.vp_registry.get_record_by_view(my_child_view)

        assert test_record == child_record

        other_view = Mock()

        with raises(ValueError):
            self.vp_registry.get_record_by_view(other_view)

    def test_iteration(self):
        parent_view = Mock()
        parent_presenter = Mock()

        child_view1 = Mock()
        child_presenter1 = Mock()

        child_view2 = Mock()
        child_presenter2 = Mock()

        child_view3 = Mock()
        child_presenter3 = Mock()

        self.vp_registry.new_record(view=child_view1, presenter=child_presenter1)
        self.vp_registry.new_record(view=child_view2, presenter=child_presenter2)
        self.vp_registry.new_record(view=child_view3, presenter=child_presenter3)

        expect = [
            (child_view1, child_presenter1),
            (child_view2, child_presenter2),
            (child_view3, child_presenter3)
        ]

        for record in self.vp_registry:
            expect.remove((record.view, record.presenter))

        assert len(expect) == 0

        other_view = Mock()

    def test_len(self):
        assert len(self.vp_registry) == 0

        my_view = Mock()

        self.vp_registry.new_record(view=my_view, presenter=Mock())

        assert len(self.vp_registry) == 1

    def test_bool(self):
        assert bool(self.vp_registry)


class TestVPRecord:
    def setup(self):
        self.vp_registry = VPRegistry()

        self.vp_record = self.vp_registry.new_record(view=Mock(), presenter=Mock())

    def test_parent(self):
        child_record = self.vp_record.new_record(view=Mock(), presenter=Mock())

        assert child_record.parent == self.vp_record

    def test_kill(self):
        assert not self.vp_record.dead

        self.vp_record.dead = True

        assert self.vp_record.dead

    def test_family_dead_and_cleanup(self):
        child_record1 = self.vp_record.new_record(view=Mock(), presenter=Mock())
        child_record2 = self.vp_record.new_record(view=Mock(), presenter=Mock())

        grandchild_record = child_record2.new_record(view=Mock(), presenter=Mock())

        assert len(self.vp_record) == 2

        self.vp_record.dead = True
        child_record1.dead = True
        child_record2.dead = True

        assert len(self.vp_record) == 1
        assert not self.vp_record.family_dead
        grandchild_record.dead = True

        assert len(self.vp_record) == 0
        assert self.vp_record.family_dead
