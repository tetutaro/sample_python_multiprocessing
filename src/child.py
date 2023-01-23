#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
The module defines the Child class
which implements the actual task handling only

タスクの実際の処理だけを実装した Child class を定義するモジュール
"""
from __future__ import annotations
from typing import TypedDict
import time
from random import random
from logging import Logger

from src.dto import TaskRequest, TaskResponse


class ChildProps(TypedDict):
    """The class for Parent class to pass information
    that is necessary for task handling to Child class.
    It is given to the Child class when creating an instance.
    It is defined in TypedDict
    because it does not define the interprocess communication.

    Parent class がタスク処理に必要な情報を Child class に渡すための class。
    Child class のインスタンスを作る時に与えられる。
    プロセス間通信を定義するものではないため、TypedDict で定義した。

    Args:
        dummy_int (int): information for task handling (dummy)
        dummy_str (str): information for task handling (dummy)
    """

    dummy_int: int
    dummy_str: str


class Child:
    """The class that implements the actual task handling only.

    タスクの実際の処理だけを実装したクラス

    Args:
        dummy_int (int): information for task handling (dummy)
        dummy_str (str): information for task handling (dummy)
        logger (Logger): the root logger (single process)
                         the queue logger (multi processes)
    """

    def __init__(
        self: Child,
        dummy_int: int,
        dummy_str: str,
        logger: Logger,
    ) -> None:
        self.logger: Logger = logger
        return

    def run(self: Child, req: TaskRequest) -> TaskResponse:
        """The actual task handling.

        タスクの実際の処理

        Args:
            req (TaskRequest): the request of the task

        Returns:
            TaskResponse: the response (result) of the task

        Raises:
            ValueError: indicates the task handling is failed
        """
        # The Task
        req_index = req.request_index
        req_value = req.request_value
        res_value = req_value**2
        # Sleep a little
        time.sleep(2 * random() + 1)
        self.logger.debug(f"req({req_index}): {req_value} -> {res_value}")
        try:
            res: TaskResponse = TaskResponse(
                request_index=req_index,
                response_value=res_value,
                is_success=True,
            )
        except ValueError as e:
            # Exception is thrown on purpose to ensure Pydantic's behavior
            # and to implement error handling.
            self.logger.warning(e)
            self.logger.warning("ignore")
            raise e
        return res
