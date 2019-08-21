#!/usr/bin/env python2

import sys
from argparse import ArgumentParser
from common.logger import init_logger
from common.config import Config, VMArch
from lib.process_checker import ProcessChecker
from lib.libvirt_manager import LibvirtManager
from lib.memory_dumper import MemoryDumper


def arg_parser():
    # create the top-level parser
    parser = ArgumentParser()
    parser.add_argument('--foo', action='store_true', help='help for foo arg.')
    subparsers = parser.add_subparsers(help='You can analysis with running VMs or create a new VM')

    # create the parser for the "command_1" command
    parser_a = subparsers.add_parser('run', help='Analysis for running VMs')
    vm_group = parser_a.add_argument_group('run')
    group_ex = vm_group.add_mutually_exclusive_group()
    group_ex.add_argument("-a", dest='a', action='store_true', default=False, help='All VM')
    group_ex.add_argument("-vm", type=str, action="store", default="", help="The VM you want to analysis")

    # create the parser for the "command_2" command
    parser_b = subparsers.add_parser('new', help='Create a VM')
    parser_b.add_argument('-b', type=str, help='help for b')
    parser_b.add_argument('-c', type=str, action='store', default='', help='test')

    parser.print_help()
    print ""
    parser.parse_args(['run', '-h'])


if __name__ == "__main__":
    init_logger()
    arg_parser()
    exit()
    manager = LibvirtManager()
    #manager.create_vm(VMArch.x86_64.value, "vm3")
    #exit()

    vm_list = manager.get_running_vm()
    for key, vm in vm_list.items():
        memory_dumper = MemoryDumper(vm_list[key], interval=10, times=5)

        process_checker = ProcessChecker(vm_list[key], callback=memory_dumper.start)
        process_checker.start()


