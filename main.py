#!/usr/bin/env python2

from common.command import command
from common.logger import setup_logger, init_logger
from common.config import VMArch
from lib.process_checker import ProcessChecker
from lib.libvirt_manager import LibvirtManager

"""note: LiME socket port already used after """

if __name__ == "__main__":
    init_logger()
    #vm_name = "vm2"
    #checkers = ProcessChecker(vm_name)
    #checkers.start()

    #print command("virsh --connect qemu:///system list")
    #print command("virsh --connect qemu:///system  console %s" % vm_name)
    #print command("ls")

    manager = LibvirtManager()
    # print [vm.name() for id, vm in manager.get_running_vm().items()]
    manager.create_vm(VMArch.x86_64, "vm4")
