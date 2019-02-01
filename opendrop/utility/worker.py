import queue
import threading
from typing import TypeVar, Generic, Callable, Tuple, Union

JobIDType = TypeVar('JobIDType')
ResultType = TypeVar('ResultType')
ContainerJobIDType = TypeVar('ContainerJobIDType')
ContainerResultType = TypeVar('ContainerResultType')


class WorkerThread(Generic[JobIDType, ResultType], threading.Thread):
    class Full(Exception):
        pass

    class Empty(Exception):
        pass

    class _JobContainer(Generic[ContainerJobIDType, ContainerResultType]):
        def __init__(self, identifier: ContainerJobIDType, job: Callable[[], ContainerResultType]) -> None:
            self.identifier = identifier
            self.job = job

    class _ResultContainer(Generic[ContainerJobIDType, ContainerResultType]):
        def __init__(self, identifier: ContainerJobIDType, result: ContainerResultType) -> None:
            self.identifier = identifier
            self.result = result

    class _StopSentinel:
        pass

    _stop_sentinel = _StopSentinel()

    _InputItem = Union[_JobContainer[ContainerJobIDType, ContainerResultType], _StopSentinel]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.input = queue.Queue(maxsize=1)  # type: queue.Queue
        self.input_semaphore = threading.Semaphore(value=0)
        self.input_mutex = threading.Lock()

        self.output = queue.Queue(maxsize=1)  # type: queue.Queue
        self.output_reserved = threading.Lock()

        self._busy = False
        self._stopped = threading.Event()

    def run(self):
        while True:
            self.output_reserved.acquire()

            self.input_semaphore.acquire()
            self._busy = True

            with self.input_mutex:
                job_container = self.input.get_nowait()

            if job_container is self._stop_sentinel:
                break

            result = job_container.job()
            self._put_result(job_container.identifier, result)
            self._busy = False

    def _put_result(self, identifier: JobIDType, result: ResultType) -> None:
        if self._stopped.is_set():
            self.output_reserved.release()
            return

        self.output.put_nowait(self._ResultContainer(identifier, result))

    def put_job_override(self, identifier: JobIDType, job: Callable[[], ResultType]) -> None:
        with self.input_mutex:
            if self._stopped.is_set():
                return

            self._input_clear()
            self.input.put_nowait(self._JobContainer(identifier, job))
            self.input_semaphore.release()

    def get_result(self) -> Tuple[JobIDType, ResultType]:
        try:
            result_container = self.output.get_nowait()
        except queue.Empty:
            raise self.Empty

        self.output_reserved.release()
        return result_container.identifier, result_container.result

    def _input_clear(self) -> None:
        try:
            while self.input_semaphore.acquire(blocking=False):
                self.input.get_nowait()
        except queue.Empty:
            pass

    @property
    def has_pending_job(self) -> bool:
        return self.input.qsize() > 0

    @property
    def has_unretrieved_result(self) -> bool:
        return self.output.qsize() > 0

    @property
    def busy(self) -> bool:
        return self._busy

    def stop(self) -> None:
        with self.input_mutex:
            self._input_clear()
            self.input.put_nowait(self._stop_sentinel)
            self.input_semaphore.release()
            self._stopped.set()

        try:
            self.get_result()
        except self.Empty:
            pass

        self.join()
