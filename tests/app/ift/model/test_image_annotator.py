import math

import pytest

from opendrop.app.ift.model.image_annotator.image_annotator import IFTImageAnnotator
from opendrop.utility.geometry import Rect2


# Test validation

@pytest.fixture
def good_image_annotator():
    image_annotator = IFTImageAnnotator(lambda: (100, 100))

    image_annotator.bn_drop_region_px.set(Rect2(x=10, y=20, w=30, h=40))
    image_annotator.bn_needle_region_px.set(Rect2(x=1, y=2, w=3, h=4))
    image_annotator.bn_needle_width.set(3)

    return image_annotator


@pytest.fixture
def good_image_annotator_no_size_hint():
    image_annotator = IFTImageAnnotator(lambda: None)

    image_annotator.bn_drop_region_px.set(Rect2(x=10, y=20, w=30, h=40))
    image_annotator.bn_needle_region_px.set(Rect2(x=1, y=2, w=3, h=4))
    image_annotator.bn_needle_width.set(3)

    return image_annotator


def test_validator_accepts_valid_data(good_image_annotator):
    assert good_image_annotator.has_errors is False


@pytest.mark.parametrize('has_errors, drop_region_px', [
    (True, None),  # invalid because is None
    (True, Rect2(x=0, y=0, w=0, h=0)),  # invalid because has no finite size
    (True, Rect2(x=100, y=100, w=10, h=10)),  # invalid because outside of image extents
    (False, Rect2(x0=-30, y0=-20, x1=10, y1=10)),
    (False, Rect2(x0=-30, y0=-20, x1=110, y1=110)),
])
def test_validator_checks_drop_region(good_image_annotator, has_errors, drop_region_px):
    good_image_annotator.bn_drop_region_px.set(drop_region_px)

    assert good_image_annotator.has_errors is has_errors


# Similar to test_validator_rejects_invalid_drop_region
@pytest.mark.parametrize('has_errors, needle_region_px', [
    (True, None),
    (True, Rect2(x=0, y=0, w=0, h=0)),
    (True, Rect2(x=100, y=100, w=10, h=10)),
    (False, Rect2(x0=-30, y0=-20, x1=10, y1=10)),
    (False, Rect2(x0=-30, y0=-20, x1=110, y1=110)),
])
def test_validator_checks_needle_region(good_image_annotator, has_errors, needle_region_px):
    good_image_annotator.bn_needle_region_px.set(needle_region_px)

    assert good_image_annotator.has_errors is has_errors


@pytest.mark.parametrize('has_errors, drop_region_px', [
    (True, None),  # invalid because is None
    (True, Rect2(x=0, y=0, w=0, h=0)),  # invalid because has no finite size
    (True, Rect2(x=0, y=0, w=10, h=0)),  # invalid because has no finite size
    (True, Rect2(x=0, y=0, w=0, h=10)),  # invalid because has no finite size
    (False, Rect2(x=100, y=100, w=10, h=10)),  # assumed to be valid (not None and finite size) since no size hint.
])
def test_validator_checks_drop_region_when_no_size_hint(good_image_annotator_no_size_hint, has_errors, drop_region_px):
    good_image_annotator_no_size_hint.bn_drop_region_px.set(drop_region_px)

    assert good_image_annotator_no_size_hint.has_errors is has_errors


@pytest.mark.parametrize('has_errors, needle_region_px', [
    (True, None),  # invalid because is None
    (True, Rect2(x=0, y=0, w=0, h=0)),  # invalid because has no finite size
    (False, Rect2(x=100, y=100, w=10, h=10)),  # assumed to be valid (not None and finite size) since no size hint.
])
def test_validator_checks_needle_region_when_no_size_hint(good_image_annotator_no_size_hint, has_errors, needle_region_px):
    good_image_annotator_no_size_hint.bn_needle_region_px.set(needle_region_px)

    assert good_image_annotator_no_size_hint.has_errors is has_errors


@pytest.mark.parametrize('needle_width', [
    None,
    -1.23,
    0.0,
    math.nan,
    math.inf
])
def test_validator_rejects_invalid_needle_width(good_image_annotator, needle_width):
    good_image_annotator.bn_needle_width.set(needle_width)

    assert good_image_annotator.has_errors is True
