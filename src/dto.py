#!/usr/bin/env python
# -*- coding:utf-8 -*-
from __future__ import annotations

from pydantic import BaseModel, validator


def check_value(cls: BaseModel, value: int) -> int:
    if value < 1:
        raise ValueError(f"non-positive value: {value}")
    if value > 100:
        raise ValueError(f"value exceeds upper bound: {value}")
    return value


class TaskRequest(BaseModel):
    request_value: int
    dummy_value: int
    _q = validator("request_value", allow_reuse=True)(check_value)
    _d = validator("dummy_value", allow_reuse=True)(check_value)


class TaskResponse(BaseModel):
    request_value: int
    response_value: int
    is_success: bool
    _s = validator("response_value", allow_reuse=True)(check_value)
