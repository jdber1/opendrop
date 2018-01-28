from opendrop.utility.events.markers import handler, is_handler, get_handler_metadata, set_handler, get_handlers_from_obj


def test_set_handler_and_is_handler():
    def f():
        pass

    set_handler(f, 'source', 'name')

    assert is_handler(f)


def test_get_handler_metadata():
    def f():
        pass

    def g():
        pass

    set_handler(f, 'source1', 'name1')
    set_handler(g, 'source2', 'name2', immediate=True)

    assert get_handler_metadata(f).source_name == 'source1' \
           and get_handler_metadata(f).event_name == 'name1' \
           and get_handler_metadata(f).immediate == False

    assert get_handler_metadata(g).source_name == 'source2' \
           and get_handler_metadata(g).event_name == 'name2' \
           and get_handler_metadata(g).immediate == True


def test_handler():
    class MyClass:
        @handler('source1', 'name1', immediate=True)
        def f(self): pass

    assert is_handler(MyClass.f)

    assert get_handler_metadata(MyClass.f).source_name == 'source1' \
           and get_handler_metadata(MyClass.f).event_name == 'name1' \
           and get_handler_metadata(MyClass.f).immediate == True


def test_get_handlers_from_obj():
    class MyClass:
        @handler('name0', 'on_event0')
        def handle_name0_event0(self):
            pass

        @handler('name1', 'on_event0')
        def handle_name1_event0(self):
            pass

    assert set(get_handlers_from_obj(MyClass)) == {MyClass.handle_name0_event0, MyClass.handle_name1_event0}
