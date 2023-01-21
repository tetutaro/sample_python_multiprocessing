from _typeshed import Incomplete as Incomplete
from dto import TaskRequest as TaskRequest, TaskResponse as TaskResponse
from logging import Logger
from typing import TypedDict

class ChildProps(TypedDict):
    index: int
    dummy: str

class Child:
    index: Incomplete
    logger: Incomplete
    def __init__(self, index: int, dummy: str, logger: Logger) -> None: ...
    def run(self, req: TaskRequest) -> TaskResponse: ...
