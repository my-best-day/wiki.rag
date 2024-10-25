import time
import queue
import logging
import multiprocessing
from typing import Any
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
        logger.info(f"Initialized queued handler {name}")

    def start(self):
        if self.running:
            raise RuntimeError("Handler already running")
        self.running = True
        self.process = multiprocessing.Process(target=self._process_queue)
        logger.info(f"--> --> --> --> Starting process in {self.name}")
        self.process.start()
        logger.info(f"==> ==> ==> ==> Started process in {self.name}")

    def _process_queue(self):
        logging.basicConfig(level=logging.INFO)
        logger.info(f"*** *** *** *** Started queued handler {self.name} (running={self.running}) "
                    f"at {time.time()}")
        while self.running:
            try:
                logger.info(f"Getting payload from queue in {self.name}")
                payload = self.queue.get(timeout=2)
                if isinstance(payload, Element):
                    index = payload.index
                else:
                    index = None
                logger.info(f"Got payload from queue in {self.name} (index={index})")

                if payload is None:  # poison pill
                    self.forward(None)
                    break

                logger.info(f"Processing payload in {self.name}")
                self.forward(payload)

            except queue.Empty:
                logger.info(f"Queue empty in {self.name}")
                continue
        logger.info(f"Stopped (running={self.running}) {self.name}")

    def stop(self):
        logger.info(f"Stopping queued handler {self.name} at {time.time()}")
        if not self.running:
            return
        self.running = False
        self.queue.put(None)  # poison pill
        logger.info(f"--> --> --> --> Joining process in {self.name}")
        self.process.join()
        logger.info(f"==> ==> ==> ==> Joined process in {self.name}")

    def handle(self, payload: Any):
        logger.info(f"putting payload {payload} in queue in {self.name}")
        self.queue.put(payload)
