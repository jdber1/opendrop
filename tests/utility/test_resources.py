import gc
from unittest.mock import patch, Mock

import pytest
from pytest import raises

from opendrop.utility.resources import Resource, ResourceToken


@pytest.fixture
def TestResource():
    class TestResource(Resource):
        init_count = 0
        destroy_count = 0

        var1 = 0

        def __init__(self):
            TestResource.init_count += 1

        def teardown(self):
            TestResource.destroy_count += 1

        def method1(self):
            self.var1 += 1

    return TestResource


def test_resource_init_kwargs(TestResource):
    m = Mock(return_value=None)

    with patch.object(TestResource, '__init__', m):
        test_res_token = ResourceToken(TestResource, arg0='Apple', arg1='pie')
        test_res_token.acquire()

        m.assert_called_with(arg0='Apple', arg1='pie')


def test_resource_lifecycle(TestResource):
    assert TestResource.init_count == 0

    test_res_token = ResourceToken(TestResource)

    test_res1 = test_res_token.acquire()

    assert TestResource.init_count == 1

    test_res2 = test_res_token.acquire()

    assert TestResource.init_count == 1

    test_res1.release()

    assert TestResource.destroy_count == 0

    test_res2.release()

    assert TestResource.destroy_count == 1


def test_resource_gc_collect(TestResource):
    test_res_token = ResourceToken(TestResource)

    test_res1 = test_res_token.acquire()

    assert TestResource.init_count == 1

    del test_res1

    gc.collect()

    assert TestResource.destroy_count == 1


def test_resource_call_teardown(TestResource):
    test_res_token = ResourceToken(TestResource)

    test_res = test_res_token.acquire()

    # Shouldn't be able to call `teardown()` on a resource (since it destroys the underlying resource), use `release()`
    # instead as that utilises reference counting to determine when to destroy the resource.
    with raises(ValueError):
        test_res.teardown()


def test_resource_multiple_release(TestResource):
    test_res_token = ResourceToken(TestResource)

    test_res = test_res_token.acquire()

    test_res.release()

    with raises(ValueError):
        test_res.release()


def test_resource_wrapper_attribute_access(TestResource):
    test_res_token = ResourceToken(TestResource)

    test_res1 = test_res_token.acquire()
    test_res2 = test_res_token.acquire()

    assert test_res1.var1 == test_res2.var1 == 0

    test_res1.method1()
    test_res2.method1()

    assert test_res1.var1 == test_res2.var1 == 2


def test_resource_wrapper_proxy(TestResource):
    test_res_token = ResourceToken(TestResource)

    test_res = test_res_token.acquire()

    _test_object_proxy(test_res, TestResource)


def test_resource_token_access(TestResource):
    test_res_token = ResourceToken(TestResource)

    test_res = test_res_token.acquire()

    assert test_res.token == test_res_token


def _test_object_proxy(proxy, target_cls):
    assert isinstance(proxy, target_cls)
    assert issubclass(type(proxy), target_cls)
    assert type(proxy) == target_cls
