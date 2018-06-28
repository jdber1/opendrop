import os
from typing import Optional, Any

from opendrop.image_filter.bases import ImageFilter
from opendrop.image_filter.image_filter_group import ImageFilterGroup
from tests import samples

SAMPLES_DIR = os.path.dirname(samples.__file__)


class MyImageFilter(ImageFilter):
    def __init__(self, name: Any, z_index: Optional[int] = None) -> None:
        self.name = name  # type: Any

        if z_index is not None:
            self.z_index = z_index  # type: z_index

    def apply(self, image: 'MyTestImage') -> 'MyTestImage':
        image.touched_by.append(self.name)

        return image


class MyTestImage:
    def __init__(self):
        self.touched_by = []


class TestImageFilterGroup:
    def setup(self):
        self.image = MyTestImage()
        self.image_filter_group = ImageFilterGroup()

    def test_no_filters(self):
        self.image_filter_group.apply(self.image)

        assert self.image.touched_by == []

    def test_remove(self):
        f1 = MyImageFilter(1)
        f2 = MyImageFilter(2)

        self.image_filter_group.add(f1)
        self.image_filter_group.add(f2)

        self.image_filter_group.remove(f1)

        self.image_filter_group.apply(self.image)

        assert self.image.touched_by == [2]

    def test_add_and_z_index_ordering(self):
        filters = [
            MyImageFilter(7, z_index=4),
            MyImageFilter(2, z_index=-1),
            MyImageFilter(8, z_index=5),
            MyImageFilter(1, z_index=-2),

            MyImageFilter(5, z_index=2),
            MyImageFilter(6, z_index=2),
            MyImageFilter(3),
            MyImageFilter(4)
        ]

        for f in filters:
            self.image_filter_group.add(f)

        self.image_filter_group.apply(self.image)

        assert self.image.touched_by == [1, 2, 3, 4, 5, 6, 7, 8]
