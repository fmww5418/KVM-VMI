
import libvirt
import sys
import os
import math
import logging
from functools import wraps
from common.logger import setup_logger, init_logger
from common.config import VMArch, Config
from common.command import command


class LibvirtManager:

    def __init__(self, target="qemu:///system"):
        self._target = target
        self._conn = None
        self._logger = setup_logger('manager', 'manager.log')
        self.show_host_info()

    def _connection(func):
        """This is a decorator that open libvirt before running function and
         close after finished"""
        @wraps(func)
        def wrapper(inst, *args, **kwargs):
            inst.open()
            result = func(inst, *args, **kwargs)
            inst.close()
            return result
        return wrapper

    def open(self):
        self._conn = libvirt.open(self._target)

        if self._conn is None:
            self._logger.error('Failed to open connection to qemu:///system')
            exit(1)

    def close(self):
        self._conn.close()

    def _copy_disk(self, arch, vm_name):
        self._logger.debug('copying a new disk.. %s' % arch.value)
        src_disk = Config.get_src_disk_path(arch)
        dst_disk = Config.get_disk_path(arch, vm_name)

        if not os.path.exists(dst_disk):
            command('cp %s %s' % (src_disk, dst_disk))
        else:
            self._logger.error('disk [%s] already exist.' % dst_disk)

        return dst_disk

    def create_vm(self, arch, vm_name):

        if self.vm_is_exist(vm_name):
            self._logger.error('VM [%s] already exist.' % vm_name)
            return

        disk_path = self._copy_disk(arch, vm_name)
        kernel_path = Config.get_kernel_path(arch)
        ram = Config.get_ram_size(arch)

        if arch == VMArch.x86_64:
            create_cmd = 'sudo virt-install --connect %s --name %s'\
                         ' --ram %s --arch x86_64' \
                         ' --disk %s,bus=virtio,format=raw' \
                         ' --boot kernel=%s,kernel_args="root=/dev/vda"' \
                         ' --network network=default' \
                         ' --hvm --noautoconsole --serial pipe,path=/tmp/%s-pipe' \
                         % (self._target, vm_name, ram, disk_path, kernel_path, vm_name)

        self._logger.info('creating VM [%s] ...' % vm_name)
        self._logger.debug(create_cmd)
        self._logger.debug(command(create_cmd, timeout=0))

        return

    def vm_is_exist(self, name):
        vm_list = self.get_running_vm()
        vm_list.update(self.get_inactive_vm())
        return name in vm_list

    def create_pipe(self, name):
        pipe = ["/tmp/{0}-pipe.in", "/tmp/{0}-pipe.out"]
        self._logger.info('creating pipe ..')

        for i, s in enumerate(pipe):
            pipe[i] = s.format(name)
            if not os.path.exists(pipe[i]):
                command('mkfifo %s' % pipe[i], timeout=5)
            else:
                self._logger.error('pipe [%s] already exist.' % pipe[i])

        return

    @property
    def conn(self):
        return self._conn

    @_connection
    def get_running_vm(self):
        """
        Get all running vm.
        :return: virDomain object
        """
        vm_dict = dict()

        for vm_id in self._conn.listDomainsID():
            vm_dict[self._conn.lookupByID(vm_id).name()] = self._conn.lookupByID(vm_id)

        return vm_dict

    @_connection
    def get_inactive_vm(self):
        """
        Get all inactive vm.
        :return: virDomain object
        """
        vm_dict = dict()

        for name in self._conn.listDefinedDomains():
            vm_dict[name] = self._conn.lookupByName(name)

        return vm_dict

    @_connection
    def show_host_info(self):
        hostname = self._conn.getHostname()
        vcpus = self._conn.getMaxVcpus(None)
        nodeinfo = self._conn.getInfo()
        version = self._conn.getVersion()
        lib_version = self._conn.getLibVersion()
        self._logger.info("Libvirt Manager Init.. [ver:%s, libver:%s] [%s - #cpu:%s, vcpu:%d, mem:%sMB]" %
                          (version, lib_version, hostname, nodeinfo[2], vcpus, nodeinfo[1]))


if __name__ == "__main__":
    init_logger()
    manager = LibvirtManager()
    #print [vm.name() for id, vm in manager.get_running_vm().items()]
    manager.create_vm(VMArch.x86_64, "vm3")

    