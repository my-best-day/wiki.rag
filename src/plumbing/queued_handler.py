import queue
import logging
import multiprocessing
from typing import Any
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

    def handle(self, payload: Any):
        self.queue.put(payload)
