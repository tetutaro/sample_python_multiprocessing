#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from __future__ import annotations
from typing import List
import sys
from logging import Logger, getLogger, Formatter, StreamHandler, ERROR

import pytest

from src.parent import Parent


@pytest.fixture
def get_logger() -> Logger:
    logger: Logger = getLogger()
    logger.setLevel(ERROR)
    formatter: Formatter = Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )
    handler: StreamHandler = StreamHandler(stream=sys.stdout)
    handler.setLevel(ERROR)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


class TestParent:
    def test_singleprocess(self: TestParent, get_logger: Logger) -> None:
        parent: Parent = Parent(nchild=1, logger=get_logger)
        results: List[int] = parent.run()
        for i, res in enumerate(results):
            assert res == (i + 1) ** 2
        return

    def test_multiprocess(self: TestParent, get_logger: Logger) -> None:
        parent: Parent = Parent(nchild=2, logger=get_logger)
        results: List[int] = parent.run()
        for i, res in enumerate(results):
            assert res == (i + 1) ** 2
        return

    def test_nchild(self: TestParent, get_logger: Logger) -> None:
        parent: Parent = Parent(nchild=2, logger=get_logger)
        ret: int = parent._get_nchild(nchild=0, cpu_count=None)
        assert ret == 1
        ret = parent._get_nchild(nchild=0, cpu_count=0)
        assert ret == 1
        ret = parent._get_nchild(nchild=0, cpu_count=1)
        assert ret == 1
        ret = parent._get_nchild(nchild=0, cpu_count=2)
        assert ret == 1
        ret = parent._get_nchild(nchild=0, cpu_count=3)
        assert ret == 1
        ret = parent._get_nchild(nchild=1, cpu_count=None)
        assert ret == 1
        ret = parent._get_nchild(nchild=1, cpu_count=0)
        assert ret == 1
        ret = parent._get_nchild(nchild=1, cpu_count=1)
        assert ret == 1
        ret = parent._get_nchild(nchild=1, cpu_count=2)
        assert ret == 1
        ret = parent._get_nchild(nchild=1, cpu_count=3)
        assert ret == 1
        ret = parent._get_nchild(nchild=2, cpu_count=None)
        assert ret == 1
        ret = parent._get_nchild(nchild=2, cpu_count=0)
        assert ret == 1
        ret = parent._get_nchild(nchild=2, cpu_count=1)
        assert ret == 1
        ret = parent._get_nchild(nchild=2, cpu_count=2)
        assert ret == 1
        ret = parent._get_nchild(nchild=2, cpu_count=3)
        assert ret == 2
        ret = parent._get_nchild(nchild=2, cpu_count=4)
        assert ret == 2
        ret = parent._get_nchild(nchild=-1, cpu_count=None)
        assert ret == 1
        ret = parent._get_nchild(nchild=-1, cpu_count=0)
        assert ret == 1
        ret = parent._get_nchild(nchild=-1, cpu_count=1)
        assert ret == 1
        ret = parent._get_nchild(nchild=-1, cpu_count=2)
        assert ret == 1
        ret = parent._get_nchild(nchild=-1, cpu_count=3)
        assert ret == 2
        ret = parent._get_nchild(nchild=-1, cpu_count=4)
        assert ret == 3
        return
