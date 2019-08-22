#!/usr/bin/env python2

import sys
import signal
import logging
from argparse import ArgumentParser
from common.config import Config
from common.logger import init_logger
from common.config import Config, VMArch, EnvType
from lib.process_checker import ProcessChecker
from lib.libvirt_manager import LibvirtManager
from lib.memory_dumper import MemoryDumper

memory_dumper = list()
process_checker = list()


def exit(signum, frame):
    for checker in process_checker:
        checker.stop()
    for dumper in memory_dumper:
        dumper.stop()
    sys.exit(0)

def arg_parser():
    project_name = "%s - %s" % (Config.get_value(EnvType.PROJECT.value), Config.get_value(EnvType.VERSION.value))

    # create the top-level parser
    parser = ArgumentParser()
    parser.add_argument('--version', action='version', version=project_name)
    subparsers = parser.add_subparsers(help='You can analyze with running VMs or create VMs')

    # create the parser for the "run" command
    parser_run = subparsers.add_parser('run', help='Analysis for running VMs')
    parser_run.set_defaults(which='run')
    group_run = parser_run.add_argument_group('run')
    group_run_ex = group_run.add_mutually_exclusive_group()
    group_run_ex.add_argument('-a', '--all', dest='allvm', action='store_true', default=False, help='All VM')
    group_run_ex.add_argument('-v', '--vm', dest='vm', type=str, action='store', default='', help='The VM you want to analysis')

    # create the parser for the "create" command
    parser_create = subparsers.add_parser('create', help='Create VMs')
    parser_create.set_defaults(which='create')
    parser_create.add_argument('name', type=str, help='The VM name you want to create')
    parser_create.add_argument('architecture', type=str, help='The VM architecture you want to create')
    parser_create.add_argument('-m', '--amount', type=int, action='store', default=1, help='The VM amount you want to create')

    args = parser.parse_args()

    if args.which == 'run':
        if not args.allvm and args.vm == '':
            parser_run.print_usage()
            print "%s run: error: you have to select either of -a and -v" % __file__
            sys.exit(2)
    elif args.which == 'create':
        if not Config.arch_is_available(args.architecture):
            parser_create.print_usage()
            print "%s create: error: your arch %s is not support" % (__file__, args.architecture)
            sys.exit(2)
    return args


if __name__ == "__main__":
    init_logger()
    args = arg_parser()

    # test
    #args = arg_parser(['run', '-a'])

    manager = LibvirtManager()

    if args.which == 'create':
        for i in range(args.amount):
            if i:
                vm_name = "%s%d" % (args.name, i+1)
            else:
                vm_name = args.name

            if manager.vm_is_exist(vm_name):
                print "Cannot create VM [%s], it already exist." % vm_name
                sys.exit(2)
            else:
                manager.create_vm(args.architecture, vm_name)

    elif args.which == 'run':
        vm_list = manager.get_running_vm()

        if args.vm:
            if args.vm in vm_list:
                vm_list = {vm_list[args.vm].name: vm_list[args.vm]}
            else:
                print "Cannot find running VM [%s], it's not exist." % args.vm
                sys.exit(2)

        signal.signal(signal.SIGINT, exit)
        signal.signal(signal.SIGTERM, exit)

        for key, vm in vm_list.items():
            memory_dumper.append(MemoryDumper(vm_list[key], interval=10, times=5))

            process_checker.append(ProcessChecker(vm_list[key], callback=memory_dumper[-1].start))
            process_checker[-1].start()
