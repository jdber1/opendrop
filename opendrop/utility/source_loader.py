from abc import ABCMeta, abstractmethod
import bisect
from six import add_metaclass

import timeit
import threading

import cv2
from PIL import Image

from opendrop.constants import ImageSourceOption

from opendrop.utility.vectors import Vector2
from opendrop.utility.events import WaitLock

class Throttler(object):
    """
        Throttler class, used for regulating the pace of a loop. Initialise with an 'interval'
        parameter that specifies the target duration of a loop and call Throttler.lap(), to return
        the needed wait time in seconds tha the loop should hold for to meet the average interval
        time specified. .lap() may return a negative value if the interval given is too short or
        the loop is taking too long to execute.

        Example:

            import random, time

            throttler = Throttler(1)

            for i in range(10):
                # Some task that takes an indeterminant amount of time
                time.sleep(random.uniform(0, 0.5))

                time.sleep(max(0, throttler.lap()))

                print(i)

    """
    def __init__(self, interval):
        self.target_avg_lap_time = interval

        self.lap_start = None
        self.split = 0

    def lap(self):
        if self.lap_start is not None:
            lap_time = timeit.default_timer() - self.lap_start

            self.split += lap_time - self.target_avg_lap_time

            self.lap_start = timeit.default_timer()

            return self.target_avg_lap_time - self.split
        else:
            self.lap_start = timeit.default_timer()
            return self.target_avg_lap_time

class FrameIterator(object):
    def __init__(self, image_source, num_frames = None, interval = None):
        self.image_source = image_source

        self.frames_left = num_frames
        self.interval = interval

        self.start_time = timeit.default_timer()

        self.throttler = interval and Throttler(interval)

         # Initialises locked, first call to read_next_image will unlock it
        self.wait_lock = WaitLock()

        self.queued_image = None
        self.queued_image_timestamp = 0

        # Prepare the first image
        self.prepare_next()

        # Make sure prepare_next was successful
        if self.queued_image:
            # Timestamp offset is used to offset the first image's timestamp to 0
            self.timestamp_offset = -self.queued_image_timestamp

    def prepare_next(self):
        try:
            if self.frames_left is None or self.frames_left > 0:
                self.queued_image_timestamp, self.queued_image = self.image_source.read()
                if self.frames_left: self.frames_left -= 1
            else:
                raise ValueError
        except ValueError:
            self.queued_image_timestamp, self.queued_image = None, None
        finally:
            self.wait_lock.unlock()

    def __iter__(self):
        return self

    def __next__(self):
        if self.wait_lock.is_locked():
            raise ValueError("Can't get next value, wait_lock is still locked")
        if self.queued_image is None:
            if self.frames_left:
                raise ValueError("FrameIterator terminated early")
            else:
                raise StopIteration

        self.wait_lock.lock()

        return_values = (
            self.queued_image_timestamp + self.timestamp_offset,
            self.queued_image,
            self.wait_lock
        )

        if isinstance(self.image_source, LiveSource):
            hold_for = self.throttler and self.throttler.lap() or 0
            if hold_for < 0:
                print(
                    "[WARNING] Iterator not keeping up with specified interval ({}s behind)"
                    .format(-hold_for)
                )
            threading.Timer(hold_for, self.prepare_next).start()
        elif isinstance(self.image_source, RecordedSource):
            hold_for = self.interval
            if hold_for is not None:
                self.image_source.advance(hold_for)
            else:
                self.image_source.scrub(timeit.default_timer() - self.start_time)

            threading.Thread(target=self.prepare_next).start()

        return return_values

    # For Python2 support
    next = __next__

class FrameIterable(object):
    def __init__(self, image_source, **opts):
        self.image_source = image_source

        self.opts = opts

    def __iter__(self):
        return FrameIterator(self.image_source, **self.opts)

@add_metaclass(ABCMeta)
class ImageSource(object):
    def __init__(self):
        self.released = False

    def frames(self, *args, **kwargs):
        return FrameIterable(self, *args, **kwargs)

    @property
    def size(self):
        # May not be the most optimized way to retrieve size of a source but unless another method
        # is overriden, this will do.
        timestamp, image = self.read()
        if image:
            with image as image:
                return Vector2(image.size)
        else:
            return Vector2(0, 0)

    @abstractmethod
    def read(self):
        if self.released:
            raise ValueError(
                "Can't read from {}, object is released".format(self.__class__.__name__)
            )

    @abstractmethod
    def release(self):
        print("[DEBUG] Releasing {}".format(self.__class__.__name__))
        self.released = True

@add_metaclass(ABCMeta)
class LiveSource(ImageSource):
    def __init__(self, **kwargs):
        super(LiveSource, self).__init__(**kwargs)

@add_metaclass(ABCMeta)
class RecordedSource(ImageSource):
    def __init__(self, loop=False, **kwargs):
        super(RecordedSource, self).__init__(**kwargs)

        self.emulated_time = 0

        self.loop = loop

    @abstractmethod
    def advance(self, by): pass

    @abstractmethod
    def scrub(self, to): pass

class USBCameraSource(LiveSource):
    MAX_RETRY_READ_ATTEMPTS = 5

    def __init__(self, camera_index, **kwargs):
        super(USBCameraSource, self).__init__(**kwargs)

        self.busy = threading.Lock()

        with self.busy:
            self.vc = cv2.VideoCapture(0)

            if not self.vc.isOpened():
                raise ValueError(
                    "OpenCV failed to create a VideoCapture on index {}".format(camera_index)
                )

        print("[DEBUG] VideoCapture started, {0}x{1}".format(*self.size))

    # @property
    # def size(self):
    #     # REMOVE ME IF NOT WORKING (these constants are defined differently sometimes apparently..)
    #     with self.lock:
    #         return Vector2(
    #             self.vc.get(cv2.CAP_PROP_FRAME_WIDTH),
    #             self.vc.get(cv2.CAP_PROP_FRAME_HEIGHT)
    #         ).round_to_int()

    def read(self):
        with self.busy:
            super(USBCameraSource, self).read()

            for i in range(self.MAX_RETRY_READ_ATTEMPTS):
                # Sometimes VideoCapture fails to read, so just retry a few times
                rval, im_array = self.vc.read()
                timestamp = timeit.default_timer()
                if rval:
                    # Pixel array comes in at BGR format, Pillow expects RGB
                    im_array = cv2.cvtColor(im_array, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(im_array)
                    return timestamp, image
                else:
                    print("[DEBUG] VideoCapture failed, retrying...({})".format(i))

            raise ValueError(
                "OpenCV VideoCapture failed to read image"
            )

    def release(self):
        with self.busy:
            super(USBCameraSource, self).release()
            self.released = True
            self.vc.release()

class LocalImages(RecordedSource):
    def __init__(self, filenames, timestamps=None, interval=None, **kwargs):
        super(LocalImages, self).__init__(**kwargs)

        if not isinstance(filenames, (tuple, list)):
            filenames = (filenames,)

        if timestamps is None:
            if interval is None:
                raise ValueError(
                    "Must specify 'timestamps' or 'interval'"
                )

            timestamps = list(i*interval for i in range(len(filenames)))
        elif timestamps[0] != 0:
                raise ValueError(
                    "'timestamps' must be begin with 0"
                )

        self.filenames = filenames
        self.timestamps = timestamps

    def index_from_timestamp(self, timestamp):
        if len(self.filenames) == 1:
            return 0
        else:
            if self.loop:
                timestamp %= self.timestamps[-1]

                index = bisect.bisect(self.timestamps, timestamp) - 1

        return index

    def read(self):
        super(LocalImages, self).read()

        try:
            filename = self.filenames[self.index_from_timestamp(self.emulated_time)]
            timestamp = self.emulated_time

            image = Image.open(filename)
            return timestamp, image
        except IndexError:
            self.release()
            return None, None

    def advance(self, by):
        self.emulated_time += by

    def scrub(self, to):
        self.emulated_time = to

    def release(self):
        super(LocalImages, self).release()
        # No need to release anything


def load(desc, source_type, **opts):
    if source_type == ImageSourceOption.LOCAL_IMAGES:

        return LocalImages(filenames=desc, **opts)

    elif source_type == ImageSourceOption.USB_CAMERA:

        return USBCameraSource(camera_index=desc, **opts)

    elif source_type == ImageSourceOption.FLEA3:

        raise NotImplementedError
