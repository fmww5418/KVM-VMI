#!/usr/bin/env python2

from common.command import command
from common.logger import setup_logger, init_logger
from common.config import VMArch
from lib.process_checker import ProcessChecker
from lib.libvirt_manager import LibvirtManager


if __name__ == "__main__":
    init_logger()
    #checkers = ProcessChecker('x86_64-vm')
    #checkers.start()
    manager = LibvirtManager()
    manager.create_pipe("vm2")
    # print [vm.name() for id, vm in manager.get_running_vm().items()]
    manager.create_vm(VMArch.x86_64, "vm2")
