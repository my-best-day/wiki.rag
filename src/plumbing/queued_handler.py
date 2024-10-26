import queue
import logging
import multiprocessing
from typing import Any, Optional, List
from gen.element.element import Element
from plumbing.handler import Handler
from plumbing.chainable import Chainable


logger = logging.getLogger(__name__)


class QueuedHandler(Handler, Chainable):
    """
    A QueuedHandler is a Handler that processes elements from a queue in a separate process.
    """
    def __init__(self, name: str):
        Handler.__init__(self)
        Chainable.__init__(self)
        self.name = name
        self.queue = multiprocessing.Queue()
        self.running = False
        self.process = None

    def start(self):
        if self.running:
            raise RuntimeError("Handler already running")
        self.running = True
        self.process = multiprocessing.Process(target=self._process_queue)
        self.process.start()

    def _process_queue(self):
        logging.basicConfig(level=logging.INFO)
        while self.running:
            try:
                payload = self.queue.get(timeout=2)

                if payload is None:  # poison pill
                    self.forward(None)
                    break

                self.forward(payload)

            except queue.Empty:
                continue

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.queue.put(None)  # poison pill
        self.process.join()

    def handle(self, payload: Any) -> None:
        self.queue.put(payload)


class JsonQueuedHandler(QueuedHandler):
    """
    A QueuedHandler that handles JSON strings.
    multiprocessing.Queue pickle / unpickle the json string on the wire.
    """
    def handle(self, payload: Any):
        json_string = payload.to_json() if isinstance(payload, Element) else payload
        self._handle_json(json_string)

    def _handle_json(self, json_string: Optional[str]):
        self.queue.put(json_string)

    def forward(self, payload: Any) -> None:
        if self.next:
            payload = Element.hierarchy_from_json(payload) if payload else None
            super().forward(payload)


class BatchedQueuedHandler(QueuedHandler):
    """
    A QueuedHandler that batches elements before forwarding them.
    """
    def __init__(self, name: str):
        super().__init__(name)
        self.batch_size = 20_000
        self.batch = []

    def set_batch_size(self, batch_size: int):
        self.batch_size = batch_size
        return self

    def handle(self, payload: Any):
        self.batch.append(payload)
        if len(self.batch) >= self.batch_size:
            super().handle(self.batch)
            self.batch = []

    def forward(self, batch: List[Any]) -> None:
        if self.next:
            for payload in batch:
                super().forward(payload)


class JBQueuedHandler(QueuedHandler):
    """
    A QueuedHandler that batches JSON strings before forwarding them.
    """
    def __init__(self, name: str):
        super().__init__(name)
        self.batch_size = 50_000
        self.batch = []

    def set_batch_size(self, batch_size: int):
        self.batch_size = batch_size
        return self

    def handle(self, payload: Any):
        json_string = payload.to_json() if isinstance(payload, Element) else payload
        self.batch.append(json_string)
        if len(self.batch) >= self.batch_size:
            super().handle(self.batch)
            self.batch = []

    def forward(self, batch: List[str]) -> None:
        if self.next:
            if batch is None:
                super().forward(None)
            else:
                for payload_json in batch:
                    payload = Element.hierarchy_from_json(payload_json)
                    super().forward(payload)
