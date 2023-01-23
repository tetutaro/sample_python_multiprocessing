#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
The module defines the DTO (Data Transfer Object)
for inter-process communication.

For clarity of deficition of DTO,
and easy implementation of value checking,
Use Pydantic.

Generally, the validate function of each value (attribute)
uses the pydantic.validator() function as a decorator.
But if the same type of value exists in multiple classes
and you want to reuse the validate function,
or the similar type of values are in the same class
and you want to use the same validate function for them,
I showed how to define the validate function outside the class and reuse it.

プロセス間通信の DTO (Data Transfer Object) を定義するモジュール

明瞭に、かつ値のチェックを簡単に実装するため、
Pydantic を用いる。

一般的には各々の値の validate 関数は
pydantic.validator() 関数を decorator として用いるが、
複数の class に同じ値が存在して validate 関数を再利用したい場合、
同じ class 内でも複数の attribute に対して
同じ validate 関数を利用したい場合のために、
class 外で validate 関数を定義して、それを使い回す実装を行った。
"""
from __future__ import annotations

from pydantic import BaseModel, validator


def check_value(cls: BaseModel, value: int) -> int:
    """The validate function.

    Args:
        value (int): The value to be checked

    Returns:
        int: Checked value
    """
    # Limiting the range of values to intentionally cause an error
    if value < 1:
        raise ValueError(f"non-positive value: {value}")
    if value > 100:
        raise ValueError(f"value exceeds upper bound: {value}")
    return value


class TaskRequest(BaseModel):
    """DTO for the request of the task.

    Args:
        request_index (int): The index of the request
        request_value (int): The input value of the task
    """

    request_index: int
    request_value: int
    _i = validator("request_index", allow_reuse=True)(check_value)
    _q = validator("request_value", allow_reuse=True)(check_value)


class TaskResponse(BaseModel):
    """DTO for the response of the task.

    Args:
        request_index (int): The index of the request
        response_value (int): The output value of the task (result)
        is_success (bool): Was the handling of task succeed?
    """

    request_index: int
    response_value: int
    is_success: bool
    _r = validator("request_index", allow_reuse=True)(check_value)
    _s = validator("response_value", allow_reuse=True)(check_value)
