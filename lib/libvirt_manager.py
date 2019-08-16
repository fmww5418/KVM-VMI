
import libvirt
import sys
import logging

class LibvirtManager:

    def __init__(self, target="qemu:///system"):
        self._target = target
        self._conn = None

    def open(self):
        self._conn = libvirt.open(self._target)

        if self._conn is None:
            logging.error('Failed to open connection to qemu:///system')
            exit(1)

    def close(self):
        self._conn.close()

    def get_running_vm(self):
        """
        Get all running vm.
        :return: virDomain object
        """
        self.open()
        vm_dict = dict()
        for vm_id in self._conn.listDomainsID():
            vm_dict[vm_id] = self._conn.lookupByID(vm_id)

        self.close()
        return vm_dict

    def get_inactive_vm(self):
        """
        Get all inactive vm.
        :return: virDomain object
        """
        self.open()
        vm_dict = dict()
        for vm_id in self._conn.listDefinedDomains():
            vm_dict[vm_id] = self._conn.lookupByID(vm_id)

        self.close()
        return vm_dict


manager = LibvirtManager()
