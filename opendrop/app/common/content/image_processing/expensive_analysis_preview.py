import asyncio
import functools
from abc import abstractmethod
from collections import deque
from typing import Optional, Callable, Deque, TypeVar, Generic, Sequence

import numpy as np

from opendrop.app.common.model.image_acquisition.image_acquisition import ImageAcquisitionPreview
from opendrop.mytypes import Image
from opendrop.utility.geometry import Vector2
from opendrop.utility.bindable import Bindable
from opendrop.utility.worker import WorkerThread

AnalysisResultType = TypeVar('OperationResultType')
CacheResultType = TypeVar('CacheResultType')


class ExpensiveAnalysisPreview(Generic[AnalysisResultType]):
    _CACHE_SIZE = 100
    _WORKER_POLL_INTERVAL = 0.1

    class CacheItem(Generic[CacheResultType]):
        def __init__(self, image: Image, result: CacheResultType) -> None:
            self.image = image
            self.result = result

    class CacheMiss(Exception):
        pass

    def __init__(self, preview: ImageAcquisitionPreview, do_analysis: Callable[[Image], Image]) -> None:
        self._loop = asyncio.get_event_loop()

        self._do_analysis = do_analysis
        self._preview = preview

        self.__destroyed = False
        self.__cleanup_tasks = [self._do_preview_clear]

        self._worker = WorkerThread()  # type: WorkerThread[Image, AnalysisResultType]
        self._worker.start()
        self.__cleanup_tasks.append(self._worker.stop)

        self._cache = deque(maxlen=self._CACHE_SIZE)  # type: Deque[ExpensiveAnalysisPreview.CacheItem[AnalysisResultType]]

        event_connections = [
            self._preview.on_image_changed.connect(self._hdl_preview_image_changed)]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

        self._worker_poll_handle = None  # type: asyncio.TimerHandle

        self.reanalyse()

    def _hdl_preview_image_changed(self, transition: ImageAcquisitionPreview.Transition) -> None:
        current_image = self._preview.image
        if transition is ImageAcquisitionPreview.Transition.JUMP:
            allow_stale_filter = False
        else:
            allow_stale_filter = True

        self._set_source(current_image, allow_stale_filter=allow_stale_filter)

    def reanalyse(self) -> None:
        self._cache_clear()
        self._set_source(self._preview.image, allow_stale_filter=True)

    def _set_source(self, image: Image, allow_stale_filter: bool) -> None:
        try:
            self._do_preview_done(self._cache_request(image))
        except self.CacheMiss:
            if allow_stale_filter is False:
                self._do_preview_clear()

    def _cache_clear(self) -> None:
        self._cache.clear()

    def _cache_request(self, image: Image) -> AnalysisResultType:
        try:
            return self._cache_find_item(image).result
        except self.CacheMiss:
            self._worker_put(image)
            raise

    def _worker_put(self, image: Image) -> None:
        self._worker_poll_once()
        self._worker.put_job_override(identifier=image, job=functools.partial(self._do_analysis, image))
        self._worker_schedule_poll()

    def _worker_schedule_poll(self) -> None:
        if self._worker_poll_handle is not None:
            self._worker_poll_handle.cancel()
            self._worker_poll_handle = None

        self._worker_poll_handle = self._loop.call_later(self._WORKER_POLL_INTERVAL, self._worker_poll)

    def _worker_poll(self) -> None:
        self._worker_poll_once()
        if self._worker.has_pending_job or self._worker.has_unretrieved_result or self._worker.busy:
            self._worker_schedule_poll()

    def _worker_poll_once(self) -> bool:
        try:
            self._worker_save_result()
        except WorkerThread.Empty:
            return False

        return True

    def _worker_save_result(self) -> None:
        image, result = self._worker.get_result()
        self._hdl_worker_new_result(image, result)
        self._cache_store_result(image, result)

    def _hdl_worker_new_result(self, image: Image, result: AnalysisResultType) -> None:
        self._do_preview_done(result)

    def _cache_store_result(self, image: Image, result: AnalysisResultType):
        try:
            item = self._cache_find_item(image)
            item.result = result
        except self.CacheMiss:
            self._cache_append_item(self.CacheItem(image, result))

    def _cache_find_item(self, image: Image) -> CacheItem[AnalysisResultType]:
        for item in self._cache:
            if np.array_equal(item.image, image):
                return item
        else:
            raise self.CacheMiss

    def _cache_append_item(self, item: CacheItem[AnalysisResultType]) -> None:
        self._cache.append(item)

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True

    @abstractmethod
    def _do_preview_done(self, mask: AnalysisResultType) -> None:
        pass

    @abstractmethod
    def _do_preview_clear(self) -> None:
        pass


class MaskAnalysis(ExpensiveAnalysisPreview[np.ndarray]):
    def __init__(self, mask_out: Bindable[Optional[np.ndarray]], **kwargs) -> None:
        self._mask_out = mask_out
        super().__init__(**kwargs)

    def _do_preview_done(self, mask: Optional[np.ndarray]) -> None:
        self._mask_out.set(mask)

    def _do_preview_clear(self) -> None:
        self._do_preview_done(None)


class PolylineAnalysis(ExpensiveAnalysisPreview[Sequence[Vector2[float]]]):
    def __init__(self, polyline_out: Bindable[Optional[Sequence[Vector2[float]]]], **kwargs) -> None:
        self._polyline_out = polyline_out
        super().__init__(**kwargs)

    def _do_preview_done(self, polyline: Optional[Sequence[Vector2[float]]]) -> None:
        self._polyline_out.set(polyline)

    def _do_preview_clear(self) -> None:
        self._do_preview_done(None)
