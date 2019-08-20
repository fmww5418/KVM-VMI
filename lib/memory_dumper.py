import pexpect
import logging
import re
import time
import math
import threading
from functools import wraps
from common.config import Config, x86_64, VMArch
from common.logger import init_logger
from common.command import command
from common.utils import check_and_mkdir
from common.repeat_timer import RepeatableTimer
from lib.libvirt_manager import LibvirtManager
from socket_client import download_dump

class MemoryDumper:

    def __init__(self, vm_name, ram, username, password, arch):
        self._name = vm_name
        self._username = username
        self._password = password
        self._arch = arch
        self._ram = int(ram)

        self._lime_path = Config.get_dump_path(self._arch)
        self._lime_port = Config.get_dump_port(self._arch)
        self._lime_format = Config.get_dump_format(self._arch)
        self._save_fmt_path = Config.get_save_dump_path(self._arch, self._name + "_%s")
        check_and_mkdir(self._save_fmt_path)

        self._ipv4 = self._get_ipv4()
        self._mutex = threading.Lock()
        self._timer = RepeatableTimer(15, self.dump_memory)

    def _dump_mutex(func):
        """This is a decorator that acquire mutex before running function and
         release after finished"""
        @wraps(func)
        def wrapper(inst, *args, **kwargs):
            inst._mutex.acquire()
            inst._timer.start()
            result = func(inst, *args, **kwargs)
            if result == 0:
                inst._timer.cancel()
            inst._mutex.release()
            return result
        return wrapper

    def _get_ipv4(self):
        """"""
        child = pexpect.spawn('virsh --connect qemu:///system domifaddr %s' % self._name)
        child.expect(['ipv4', pexpect.TIMEOUT, pexpect.EOF])
        ipv4 = re.search(r'((\d{1,3}.){3}\d{1,3})', child.buffer)
        child.close()
        if not ipv4:
            logging.error('Cannot get ipv4 address in VM %s' % self._name)
            return None
        return ipv4.group(0)

    @staticmethod
    def _read_lines(child):
        out = child.readline()
        while out:
            print out
            out = child.readline()

    @_dump_mutex
    def dump_memory(self):
        """Dump guest VM memory to host"""

        def child_close(c, _return=1):
            c.close()
            return _return

        """Exit if have not getting ipv4 address"""
        if not self._ipv4:
            return 0

        cmd = "virsh --connect qemu:///system console %s" % self._name
        child = pexpect.spawn(cmd, timeout=3)

        index = child.expect([pexpect.TIMEOUT, "failed to get domain", "console session exists", pexpect.EOF], timeout=1)
        if index == 0:
            x = re.search("is \^\]", child.buffer)
            if not x:
                logging.error("Virsh connect to %s timeout!" % self._name)
        elif index == 1:
            logging.error("Failed to get domain %s." % self._name)
        elif index == 2:
            logging.error("Operation failed: Active console session exists for %s." % self._name)
        else:
            logging.error("Virsh connect to %s failed!" % self._name)
        if index:
            return child_close(child, _return=0)

        child.send('\n')

        index = child.expect(["#", "login", pexpect.EOF, pexpect.TIMEOUT])

        if index == 1:
            """ login session """
            child.sendline(self._username)
            child.sendline(self._password)
            child.send('\n')

            index = child.expect(["#", "incorrect", pexpect.EOF, pexpect.TIMEOUT])
            if index == 1:
                logging.error("Login incorrect in %s with %s:%s" % (self._name, self._username, self._password))
            elif index > 1:
                logging.error("Find unknown reason in login getty of %s!" % self._name)
        elif index > 1:
            logging.error("Login failed.")

        if index == 0:
            logging.info("VM %s login successfully!" % self._name)
        else:
            return child_close(child, _return=0)

        insmod_cmd = 'insmod %s "path=tcp:%s format=%s"' % (self._lime_path, self._lime_port, self._lime_format)
        logging.debug('insmod lime.. (%s)' % insmod_cmd)
        child.sendline(insmod_cmd)
        time.sleep(1)

        save_path = self._save_fmt_path % time.strftime("%Y%m%d_%H%M%S", time.localtime())

        logging.debug('Download memory dump ..')
        download_status = download_dump(save_path, self._ipv4, self._lime_port)
        child.send('\n')

        # can't connect to server
        if not download_status:
            return child_close(child, _return=0)

        index = child.expect(["#", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            host = pexpect.spawn("ls -s %s" % save_path)
            #self._read_lines(host)
            hindex = host.expect(["cannot access", "\s%s$" % save_path, pexpect.EOF, pexpect.TIMEOUT])
            print 'a', host.buffer
            print 'b', host.before
            print 'c', host.after
            if hindex == 1:
                p = pow(2, 10)
                size = int(math.ceil(float(host.before)/p))

                if size != self._ram:
                    logging.error("The saved [%s] mem size %dM is inconsistent with VM ram size %dM." % (self._name, size, self._ram))
                else:
                    logging.info("Save VM %s memory successfully." % self._name)
            else:
                logging.info("Save VM %s memory failed." % self._name)

            host.close()
        else:
            logging.error("VM %s insmod failed." % self._name)

        child.sendline('lsmod')
        index = child.expect(["lime", pexpect.EOF, pexpect.TIMEOUT])

        if index == 0:
            child.sendline('rmmod lime')
            child.sendline('lsmod')
            print child.buffer
        else:
            logging.error("VM %s have not found lime kernel module." % self._name)

        return child_close(child, _return=1)

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.cancel()


if __name__ == "__main__":
    init_logger()
    vm_name = "vm4"

    manager = LibvirtManager()
    if not manager.vm_is_exist(vm_name):
        manager.create_vm(VMArch.x86_64, vm_name)
    time.sleep(5)

    session_manager = MemoryDumper(vm_name, Config.get_value(x86_64.RAM_SIZE.value),
                                   Config.get_value(x86_64.USERNAME.value),
                                   Config.get_value(x86_64.PASSWORD.value), VMArch.x86_64)
    #session_manager.start()
    session_manager.dump_memory()
