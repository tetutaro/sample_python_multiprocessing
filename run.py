#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import sys
from argparse import ArgumentParser, Namespace
from logging import (
    Logger,
    Formatter,
    StreamHandler,  # the main log handler
    getLogger,
    INFO,  # the Log Level
)

from src.parent import Parent

LOG_LEVEL: int = INFO


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
    _ = parent.run()
    return


if __name__ == "__main__":
    main()
