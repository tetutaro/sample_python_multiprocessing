#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from __future__ import annotations
from typing import TypedDict
import time
from random import random
from logging import Logger

from src.dto import TaskRequest, TaskResponse


class ChildProps(TypedDict):
    dummy_int: int
    dummy_str: str


class Child:
    def __init__(
        self: Child,
        dummy_int: int,
        dummy_str: str,
        logger: Logger,
    ) -> None:
        self.logger: Logger = logger
        return

    def run(self: Child, req: TaskRequest) -> TaskResponse:
        req_value = req.request_value
        res_value = req_value**2
        time.sleep(2 * random() + 1)
        self.logger.debug(f"req({req_value}) -> res({res_value})")
        try:
            res: TaskResponse = TaskResponse(
                request_value=req_value,
                response_value=res_value,
                is_success=True,
            )
        except ValueError as e:
            self.logger.warning(e)
            self.logger.warning("ignore")
            raise e
        return res
