#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""A sample implementation for creating multiple child processes
and performing distributed parallel processing.
This implementation will be useful for the case
that there are a large number of tasks with a large amount of computation.

"Parent" submits the request of the task to the Request Queue
and lets "Children" retrieve and handle the task in parallel,
then receives the result of the task in the Response Queue.
At that time, the progress bar is displayed to visualize the progress.
Logs generated in "Children" are passed to "Parent" via the Message Queue,
and "Parent" show (or store) them as usual.
"""
from __future__ import annotations
from typing import List, Optional
import os
import sys
from time import time_ns
from multiprocessing import (
    Process,  # for the process of the Child
    Queue,  # for the Message Queue
    JoinableQueue,  # for the Request Queue
    SimpleQueue,  # for the Responce Queue
    get_logger,
)
from queue import Empty  # the queue empty Exception
from argparse import ArgumentParser, Namespace
from logging import (
    Logger,
    Formatter,
    StreamHandler,  # the main log handler
    getLogger,
    INFO,  # the Log Level
)
from logging.handlers import (
    QueueHandler,  # the log handler for Child
    QueueListener,  # pass Child logs to the main log handler
)

from tqdm import tqdm  # the progress bar

from dto import (
    TaskRequest,  # the Task Request
    TaskResponse,  # the Task Response
)
from child import ChildProps, Child  # the class that handle the task

LOG_LEVEL: int = INFO  # the log level


def child_worker(
    req_queue: JoinableQueue,
    res_queue: SimpleQueue,
    log_queue: Queue,
    props: ChildProps,
) -> None:
    """the worker function

    Args:
        req_queue (JoinableQueue): the Request Queue
        res_queue (SimpleQueue): the Response Queue
        log_queue (Queue): the Message Queue
        props (Dict[str, Any]): properties of the Child
    """
    # create the logger for the Child
    logger: Logger = get_logger()
    logger.setLevel(LOG_LEVEL)
    formatter: Formatter = Formatter(f"[CHILD{props['index']:02}] %(message)s")
    handler: QueueHandler = QueueHandler(log_queue)
    handler.setLevel(LOG_LEVEL)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # create the instance of the Child
    chi: Child = Child(**props, logger=logger)
    # main loop
    while True:
        try:
            # retrieve the task request
            req: Optional[TaskRequest] = req_queue.get()
        except (Empty, ValueError):
            # The Request Queue is empty or closed
            # exit main loop
            break
        if req is None:
            # Someone (Parent or Child) tells me to close
            # tell another Child to close
            req_queue.put(None)
            # exit main loop
            break
        req_value: int = req.request_value
        try:
            # let Child handle the task
            res: TaskResponse = chi.run(req=req)
        except ValueError:
            # create error response
            res = TaskResponse(
                request_value=req_value,
                response_value=1,  # dummy value
                is_success=False,
            )
        # send the Task Response to Parent via the Response Queue
        res_queue.put(res)
        # tell this task request was done to the Request Queue
        req_queue.task_done()
    return


class Parent:
    def __init__(
        self: Parent,
        nchild: int,
        logger: Logger,
    ) -> None:
        """Parent class

        Args:
            nchild (int): the number of child processes
            logger (Logger): the main logger
        """
        self.nchild: int = self._get_nchild(
            nchild=nchild,
            cpu_count=os.cpu_count(),
        )
        self.logger: Logger = logger
        return

    def _get_nchild(
        self: Parent,
        nchild: int,
        cpu_count: Optional[int],
    ) -> int:
        # calculate the proper number of processes
        if cpu_count is None or cpu_count == 1:
            return 0
        return cpu_count - 1 if nchild < 0 or cpu_count <= nchild else nchild

    def run(self: Parent) -> None:
        num_task: int = 12
        start: int = time_ns()
        if self.nchild == 0:
            results: List[int] = self._run_single(num_task=num_task)
        else:
            results = self._run_multiple(num_task=num_task)
        end: int = time_ns()
        for i, result in enumerate(results):
            try:
                assert (
                    result == (i + 1) ** 2
                ), f"results[{i}]: expected={(i + 1)**2}, value={result}"
            except AssertionError as e:
                self.logger.error(e)
                continue
        self.logger.info(
            f"processing time: {round(float((end - start) / 1e9), 3)}s"
        )
        return

    def _run_single(self: Parent, num_task: int) -> List[int]:
        # create the Task Requests
        reqs: List[TaskRequest] = list()
        for i in range(num_task):
            try:
                req: TaskRequest = TaskRequest(
                    request_value=i,
                    dummy_value=i + 1,
                )
            except Exception as e:
                self.logger.warning(e)
                self.logger.warning("ignore")
                continue
            reqs.append(req)
        # handle tasks
        chi: Child = Child(
            index=0,
            dummy="dummy",
            logger=self.logger,
        )
        results: List[int] = list()
        self.logger.info("dispatch tasks to children")
        for req in tqdm(reqs):
            try:
                res: TaskResponse = chi.run(req=req)
            except ValueError:
                continue
            results.append(res.response_value)
        self.logger.info("children has finished tasks")
        # return results
        return results

    def _run_multiple(self: Parent, num_task: int) -> List[int]:
        # queues for inter-process communitation
        request_queue: JoinableQueue = JoinableQueue()
        result_queue: SimpleQueue = SimpleQueue()
        # push requests to request_queue in advance
        task_remains: int = 0
        for i in range(num_task):
            try:
                request_queue.put(
                    TaskRequest(
                        request_value=i,
                        dummy_value=i + 1,
                    )
                )
            except Exception as e:
                self.logger.warning(e)
                self.logger.warning("ignore")
                continue
            else:
                task_remains += 1
        # message queue for child processes
        message_queue: Queue = Queue()
        listener: QueueListener = QueueListener(
            message_queue,
            *self.logger.handlers,
            respect_handler_level=True,
        )
        listener.start()
        # kick children
        self.logger.info("dispatch tasks to children")
        procs: List[Process] = list()
        for i in range(self.nchild):
            props: ChildProps = {
                "index": i,
                "dummy": "dummy",
            }
            proc: Process = Process(
                target=child_worker,
                args=(
                    request_queue,
                    result_queue,
                    message_queue,
                    props,
                ),
            )
            procs.append(proc)
            proc.start()
        # start progress bar, receive result and update progress bar
        responses: List[TaskResponse] = list()
        pbar = tqdm(total=task_remains)
        while task_remains > 0:
            res: TaskResponse = result_queue.get()
            if res.is_success:
                responses.append(res)
            pbar.update()
            task_remains -= 1
        pbar.close()
        # wait for request queue becomes empty
        request_queue.join()
        # tell children to close
        request_queue.put(None)
        # wait for all children processes end
        for proc in procs:
            proc.join()
        # release resources
        listener.stop()
        message_queue.close()
        request_queue.close()
        result_queue.close()
        self.logger.info("children has finished tasks")
        # sort responses and return results
        return [
            res.response_value
            for res in sorted(responses, key=lambda x: x.request_value)
            if res.response_value is not None
        ]


def main() -> None:
    # get arguments
    parser: ArgumentParser = ArgumentParser(
        description="A sample implementation of multiprocessing"
    )
    parser.add_argument(
        "-n",
        "--nchild",
        type=int,
        default=-1,
        help=(
            "the number of child processes (defualt: -1 == os.cpu_count() - 1)"
        ),
    )
    args: Namespace = parser.parse_args()
    # create the main logger
    logger: Logger = getLogger()
    logger.setLevel(LOG_LEVEL)
    formatter: Formatter = Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )
    handler: StreamHandler = StreamHandler(stream=sys.stdout)
    handler.setLevel(LOG_LEVEL)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # create the Parent instance
    parent: Parent = Parent(**vars(args), logger=logger)
    # do it!
    parent.run()
    return


if __name__ == "__main__":
    main()
