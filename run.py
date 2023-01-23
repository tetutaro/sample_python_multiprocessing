#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import sys
from argparse import ArgumentParser, Namespace
from logging import (
    Logger,
    Formatter,
    StreamHandler,  # the root log handler
    getLogger,
    INFO,  # the Log Level
)

from src.parent import Parent

LOG_LEVEL: int = INFO


def main() -> None:
    # Get arguments
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
    # Create the root logger
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
    # Create the Parent instance
    parent: Parent = Parent(**vars(args), logger=logger)
    # Do it!
    _ = parent.run()
    return


if __name__ == "__main__":
    main()
