#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
The module defines the Parent class that implements parent process handling,
and the wrapper function (child_worker) that run the Child class
that implements the actual task handling.

このモジュールでは、親プロセスの処理を実装した Parent class と、
実際の Task の処理を実装した Child class を動作させる
wrapper 関数（child_worker）を定義している。
"""
from __future__ import annotations
from typing import List, Optional
import os
from time import time_ns
from multiprocessing import (
    Process,  # For the process of the Child
    Queue,  # For the Message Queue
    JoinableQueue,  # For the Request Queue
    SimpleQueue,  # For the Responce Queue
    get_logger,
)
from logging import Logger, Formatter
from logging.handlers import (
    QueueHandler,  # The log handler for Child
    QueueListener,  # Pass Child logs to the main log handler
)

from tqdm import tqdm  # The progress bar

from src.dto import (
    TaskRequest,  # The Task Request
    TaskResponse,  # The Task Response
)
from src.child import (
    ChildProps,
    Child,
)  # The class that actually handle the task


def child_worker(
    index: int,
    req_queue: JoinableQueue,
    res_queue: SimpleQueue,
    log_queue: Queue,
    log_level: int,
    props: ChildProps,
) -> None:
    """The function called from multiprocessing.Process class.

    So, this function is not an in-class function,
    must be a normal function.

    This function works in the child process.

    This function handle the every operation about
    the Request Queue and Response Queue.
    So, the Child class does not need to operate Queues at all,
    and need to handle the Task only.

    And this function create the Log Handler and the Logger
    using the Message Queue and pass it to the Child class.
    So the Child class can send logs as usual.

    This function also assumes that some error occurs
    in task handling of the Child class.
    This function recognizing the error by receiving ValueError.
    In that case, by registering the error Response to the Response Queue,
    This function tell the error to the Parent class.

    JoinableQueue.get() function receives a Task from the Request Queue.
    It is called with block=True option.
    So, it keeps waiting eternally unless it receives any entry from the Queue
    even if the Request Queue is empty or closed.
    (If use JoinableQueue.get(block=False),
    queue.Empty Exception is raised if the Queue is empty,
    ValueError Exception is raised if the Queue is closed).
    So, when all task is finished,
    Parent class sends None Entry to Request Queue,
    this function exit the main loop by receiving it.

    If this function receive None Entry with JoniableQueue.get(),
    The None Entry disappears from the Queue.
    So to terminate other Child processes,
    You have to JoinableQueue.push() a new None Entry.

    multiprocessing.Process class から呼ばれる関数。

    よって、この関数は class 内関数ではなく、
    通常の関数でなくてはならない。

    この関数は子プロセスにて動作する。

    この関数の中で Request Queue, Response Queue に関する処理を
    全て行うので、Child clas では Queue の処理を一切する必要がなく、
    Task の処理のみを行うだけでよい。

    また Message Queue を使った Log Handler および Logger の作成も
    行い、それを Child class に渡すので、
    Child class は通常と変わらずログを送ることが出来る。

    この関数では Child class の処理でエラーが発生する場合も想定している。
    ValueError を受け取ることでエラーが発生したことを認識し、
    その場合にはエラーを表す Response を Response Queue に登録することで、
    Parent class にエラーを伝えている。

    Request Queue から Task を受け取る JoinableQueue.get() 関数は
    block=True オプションを付けているので、何か Entry を受け取らない限り
    空であっても close() されてもずっと待ち続ける
    （JoinableQueue.get(block=False) の場合は、
    Queue が空の場合は queue.Empty、
    Queue が close された場合は ValueError の例外が raise される）。
    そこで、全ての処理が終了したら、
    Parent class が Request Queue に None Entry を送り、
    それを受け取ることでこの関数は main loop を終了する。

    JoniableQueue.get() で None Entry を受け取った場合には、
    その None Entry は Queue から無くなる。
    そこで他の子プロセスも終了させるために、
    新たに None Entry を JoinableQueue.push() しなければならない。

    Args:
        index (int): The index of child process
        req_queue (JoinableQueue): The Request Queue
        res_queue (SimpleQueue): The Response Queue
        log_queue (Queue): The Message Queue
        log_level (int): Rhe log level
        props (Dict[str, Any]): Properties of the Child
    """
    # Create the logger for the Child
    logger: Logger = get_logger()
    logger.setLevel(log_level)
    formatter: Formatter = Formatter(f"[CHILD{index:02}] %(message)s")
    handler: QueueHandler = QueueHandler(log_queue)
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # Create the instance of the Child
    chi: Child = Child(**props, logger=logger)
    # Main loop
    while True:
        # Retrieve the task request
        req: Optional[TaskRequest] = req_queue.get(block=True)
        if req is None:
            # Someone (Parent or Child) tells me to close
            # tell another Child to close
            req_queue.put(None)
            # exit main loop
            break
        req_index: int = req.request_index
        try:
            # Let Child handle the task
            res: TaskResponse = chi.run(req=req)
        except ValueError:
            # Create error response
            res = TaskResponse(
                request_index=req_index,
                response_value=1,  # dummy value
                is_success=False,
            )
        # Send the Task Response to Parent via the Response Queue
        res_queue.put(res)
        # Tell this task request was done to the Request Queue
        req_queue.task_done()
    return


class Parent:
    """The class that implements parent process' handling.

    Create the Request Queue, the Response Queue and the Message Queue,
    Then register all Tasks in Request Queue in advance,
    And set the Log Handler to the Message Queue
    to receive Logs from child processes.
    Pass all Queues to the wrapper function to spawn a child process,
    Receive the results of the Task processed by the child process
    in the Response Queue.

    Also, update the progress every time
    the Parent class receive the result in the Response Queue,
    Visualize its progress with Progress Bar (tqdm).

    I used the multiprocessing.Process class to create child processes.
    It can be implemented more easily by using
    the multiprocessing.Pool class.
    But you can't use multiprocessing.Pool class
    when passing Queues to the wrapper function (child_worker()).
    If you pass Queues to the wrapper function in arguments,
    You will get the following error:

        RuntimeError: JoinableQueue objects should only be shared
        between processes through inheritance

    The multiprocessing.Pool class should be used when
    the cost to prepare resources for handling tasks is low,
    and it is possible to launch child processes for each task,
    and throw them away when the task is done.

    The Request Queue is a Queue that child processes use for waiting.
    Because it is necessary to properly grasp
    the termination of the child processes,
    I used multiprocessing.JoinableQueue for the Request Queue.

    On the other hand, the Response Queue just stores results of the task
    handled by child processes,
    And only the parent process receives it.
    No control is required in comparison with the Request Queue.
    So I used multiprocessing.SimpleQueue for the Response Queue.

    Furthermore, it does not wait processes in the Message Queue,
    But I want the block function in the Message Queue
    because it is inconvenient if the order of the logs is changed.
    So I used multiprocessing.Queue for the Message Queue.

    I think that the way described above should be the proper way
    to use these three Queues.

    If you specify 1 as the number of child process,
    The parent process does not actually create a child process,
    only the parent process handle all the tasks.
    Even in that case, in the wrapper function (child_worker())
    implements all Logger settings and Queue operations,
    and the Child class only implements the actual task handling,
    So I can implement handlings in exactly the same way
    as the case of multi processes.

    Naturally, in the case of multi processes,
    in the order in which Task was added
    There is no guarantee that results will be returned.
    So if you want to get the same result as single process,
    Finally, the results should be sorted in the order requested.

    Of course, in the case of multi processes,
    there is no guarantee that results will be returned
    in the order in which tasks were added.
    So if you want to get the same result as with single process,
    you need to finally sort the results in the order you requested.

    親プロセスの処理を実装した class。

    Request Queue, Response Queue, Message Queue を作り、
    予め Task をすべて Request Queue に登録し、
    子プロセスからの Log を受け取るために
    Message Queue に対して Log Handler の設定を行い、
    すべての Queue を wrapper 関数に渡して子プロセスを立ち上げ、
    子プロセスが処理した Task の結果を Response Queue で受け取る。

    また、Response Queue で結果を受け取る毎に進捗状況を更新し、
    Progress Bar (tqdm) でその進捗状況を可視化する。

    子プロセスの生成には multiprocessing.Process class を使っている。
    multiprocessing.Pool class を用いるともっと簡単に実装できるが、
    Queue を渡しているので multiprocessing.Pool class は使用できない。
    multiprocessing.Pool class を使用して、そこから呼び出す関数
    （この場合は child_worker()）の引数に Queue を渡すと、
    以下のエラーが出る。

        RuntimeError: JoinableQueue objects should only be shared
        between processes through inheritance

    multiprocessing.Pool class は、子プロセスが処理のための資源を準備する
    コストが低く、タスク毎に子プロセスを立ち上げて処理させ使い捨てる
    実装の場合に用いるべきである。

    Request Queue は子プロセスが待ち合わせの為に使う Queue であり、
    子プロセスの終了をきちんと把握する必要があるため、
    Request Queue には multiprocessing.JoinableQueue を用いる。

    それに対し Response Queue は子プロセスが処理した結果を
    親プロセスが受け取るだけなので、何も制御がいらない。
    よって Response Queue には multiprocessing.SimpleQueue を使う。

    さらに、Message Queue でプロセスを待ち合わせることはしないが、
    ログの順番が入れ替わると不便なので block 機能はほしい。
    よって Message Queue には multiprocessing.Queue を使う。

    multiprocessing モジュールで定義されている３種類の Queue は、
    上記のように使い分けることを想定されていると考える。

    子プロセス数を 1 と指定した場合は、
    実際には子プロセスを生成せず、親プロセスだけで処理を行う。
    その場合にも、wrapper 関数（child_worker()）にて
    Logger の設定や Queue に関する処理をすべて実装し、
    Child class では実際のタスクの処理だけを実装しているため、
    multi processes の場合と全く同じ様に処理を実装することが出来る。

    当然ながら、multi processes の場合は Task を追加した順番通りに
    結果が返ってくる保証は無い。
    よって、single process の場合と同じ結果を得たい場合は、
    最終的に結果をリクエストした順番にソートする必要がある。

    Args:
        nchild (int): The number of child processes
        logger (Logger): The root logger
    """

    def __init__(
        self: Parent,
        nchild: int,
        logger: Logger,
    ) -> None:
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
        """The function that sets the number of child processes to
        at least 1 and at most the number of CPU - 1.

        子プロセスの数を最小で 1、最大で CPU数 - 1 にする関数

        Args:
            nchild (int): the indicated number of child processes
            cpu_count (Optional[int]): the number of CPU

        Returns:
            int: The proper number of child processes
        """
        if cpu_count is None or cpu_count < 2:
            return 1
        if 0 <= nchild and nchild < 2:
            return 1
        return cpu_count - 1 if nchild < 0 or cpu_count <= nchild else nchild

    def run(self: Parent) -> List[int]:
        """The wrapper function for _run_single() and _run_multiple().
        Switch which one to use by the value of self.nchild.
        Also, it measures the total time taken for the all handlings.

        _run_single() と _run_multiple() の wrapper 関数。
        self.nchild の値によってどちらを使うかを切り替える。
        また、処理にかかった時間を計測する。

        Returns:
            List[int]: The results
        """
        num_task: int = 12  # The number of tasks
        start: int = time_ns()
        if self.nchild < 2:
            results: List[int] = self._run_single(num_task=num_task)
        else:
            results = self._run_multiple(num_task=num_task)
        end: int = time_ns()
        self.logger.info(
            f"processing time: {round(float((end - start) / 1e9), 3)}s"
        )
        return results

    def _run_single(self: Parent, num_task: int) -> List[int]:
        """The function handle the tasks
        when the number of child processes is 1.
        It doesn't actually spawn a child process,
        just the parent process handle the tasks.
        Create an array of Tasks, create an instance of Child class,
        and just handle tasks in order.

        子プロセス数が 1 の場合の処理をする関数。
        実際には子プロセスを生成せず、親プロセスだけで処理する。
        Task の配列を作って、Child class のインスタンスを作り、
        Task を順番に処理するだけ。

        Args:
            num_task (int): The number of tasks

        Returns:
            List[int]: the Results
        """
        # Create the Task Requests
        reqs: List[TaskRequest] = list()
        for i in range(num_task):
            try:
                req: TaskRequest = TaskRequest(
                    request_index=i + 1,
                    request_value=i,
                )
            except ValueError as e:
                # Exception is thrown on purpose to ensure Pydantic's behavior
                # and to implement error handling.
                self.logger.warning(e)
                self.logger.warning("ignore")
                continue
            reqs.append(req)
        # Create instance of Child class
        chi: Child = Child(
            dummy_int=0,
            dummy_str="0",
            logger=self.logger,
        )
        # Handle tasks
        results: List[int] = list()
        self.logger.info("dispatch tasks to children")
        for req in tqdm(reqs):
            try:
                res: TaskResponse = chi.run(req=req)
            except ValueError:
                # Just ignore the error
                continue
            results.append(res.response_value)
        self.logger.info("children has finished tasks")
        # Return results
        return results

    def _run_multiple(self: Parent, num_task: int) -> List[int]:
        """The function that handles the tasks in the case of multi processes.

        * Create the Request Queue and the Response Queue
        * Put all Tasks in Request Queue in advance
        * Create a Message Queue
        * Create a listener that sends logs to root logger
          when they are pushed in the Message Queue
        * Create child processes and
          pass all Queue to the wrapper function (child_worker()),
          and let them run
        * Create a Progress Bar
        * When the result comes back to Response Queue,
          update the progress bar and preserving the result
        * Wait for all processing to finish and all child processes to finish
        * Free up resources
        * Sort and return results

        multi processes の場合の処理をする関数。

        * Request Queue, Response Queue を作る
        * Task を予めすべて Request Queue に入れる
        * Message Queue を作る
        * Message Queue にログが入ったらそれを root logger に流す
          listener を作る
        * 子プロセスを作り、
          すべての Queue を wrapper 関数（child_worker()）に渡して
          実行させる
        * Progress Bar を作る
        * Response Queue に結果が帰ってきたら、
          それを保持しつつ Progress Bar を更新する
        * すべての処理が終わり、子プロセスが全て終了するのを待つ
        * 資源を解放する
        * 結果をソートして返す

        Args:
            num_task (int): The number of tasks

        Returns:
            List[int]: the Results
        """
        # Queues for inter-process communitation
        request_queue: JoinableQueue = JoinableQueue()
        result_queue: SimpleQueue = SimpleQueue()
        # Push all Requests to the Request Queue in advance
        task_remains: int = 0
        for i in range(num_task):
            try:
                request_queue.put(
                    TaskRequest(
                        request_index=i + 1,
                        request_value=i,
                    )
                )
            except ValueError as e:
                # Exception is thrown on purpose to ensure Pydantic's behavior
                # and to implement error handling.
                self.logger.warning(e)
                self.logger.warning("ignore")
                continue
            else:
                task_remains += 1
        # Create the Message Queue for logs in child processes
        message_queue: Queue = Queue()
        # Create the Queue Listener
        # that throws logs pushed in the queue to root handler(s)
        listener: QueueListener = QueueListener(
            message_queue,
            *self.logger.handlers,
            respect_handler_level=True,
        )
        listener.start()
        # Kick children
        self.logger.info("dispatch tasks to children")
        procs: List[Process] = list()
        for i in range(self.nchild):
            # Properties (arguments) of Child class which is needed for
            # task handling. (dummy)
            props: ChildProps = {
                "dummy_int": i,
                "dummy_str": str(i),
            }
            # Create Child process and pass all the Queues
            proc: Process = Process(
                target=child_worker,
                args=(
                    i + 1,  # child index
                    request_queue,
                    result_queue,
                    message_queue,
                    self.logger.level,
                    props,
                ),
            )
            procs.append(proc)
            # Kick it
            proc.start()
        # Start progress bar, receive result and update progress bar
        responses: List[TaskResponse] = list()
        pbar = tqdm(total=task_remains)
        while task_remains > 0:
            res: TaskResponse = result_queue.get()
            if res.is_success:
                responses.append(res)
            pbar.update()
            task_remains -= 1
        pbar.close()
        # Wait for request queue becomes empty
        request_queue.join()
        # Tell children to close
        request_queue.put(None)
        # Wait for all child processes end
        for proc in procs:
            proc.join()
        # Release resources
        listener.stop()
        message_queue.close()
        # Request_queue.join()  # Don't do this (There is one None Entry left)
        request_queue.close()
        result_queue.close()
        self.logger.info("children has finished tasks")
        # Sort responses and return results
        return [
            res.response_value
            for res in sorted(responses, key=lambda x: x.request_index)
            if res.response_value is not None
        ]
