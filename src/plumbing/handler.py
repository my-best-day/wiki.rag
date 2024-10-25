from typing import Any
from abc import ABC, abstractmethod


class Handler(ABC):
    @abstractmethod
    def handle(self, payload: Any):
        pass
