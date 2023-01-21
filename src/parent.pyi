from _typeshed import Incomplete as Incomplete
from child import ChildProps as ChildProps
from logging import Logger
from multiprocessing import JoinableQueue, Queue, SimpleQueue

LOG_LEVEL: int

def child_worker(req_queue: JoinableQueue, res_queue: SimpleQueue, log_queue: Queue, props: ChildProps) -> None: ...

class Parent:
    nprocess: int
    logger: Incomplete
    def __init__(self, nprocess: int, logger: Logger) -> None: ...
    def run(self) -> None: ...

def main() -> None: ...
