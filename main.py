#!/usr/bin/env python2

from common.command import command
from common.logger import setup_logger, init_logger
from lib.process_checker import ProcessChecker


if __name__ == "__main__":
    init_logger()
    checkers = ProcessChecker('x86_64-vm')
    checkers.start()
