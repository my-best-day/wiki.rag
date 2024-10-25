from abc import ABC
from typing import Any, Optional
from plumbing.handler import Handler


class Chainable(ABC):
    def __init__(self):
        self.next: Optional[Handler] = None

    def chain(self, next: Handler):
        self.next = next

    def forward(self, item: Any):
        if self.next:
            self.next.handle(item)
