from typing import Callable, Any, List


class Dispatcher:
    """Base dispatcher that handles synchronous event distribution"""
    def __init__(self) -> None:
        self.handlers: List[Callable[[Any], None]] = []

    def start(self) -> None:
        self.delayed_initialization()

    def stop(self) -> None:
        pass

    def delayed_initialization(self) -> None:
        pass

    def register_handler(self, handler: Callable[[Any], None]) -> 'Dispatcher':
        self.handlers.append(handler)
        return self

    def handle(self, item: Any) -> None:
        self.call_handlers(item)

    def call_handlers(self, item: Any) -> None:
        for handler in self.handlers:
            handler(item)
