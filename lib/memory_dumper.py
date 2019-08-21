import pexpect
import logging
import re
import time
import math
import threading
from functools import wraps
from common.config import Config, x86_64, VMArch
from common.logger import init_logger
from common.utils import check_and_mkdir, kb_to_mb
from common.repeat_timer import RepeatableTimer
from lib.libvirt_manager import LibvirtManager
from socket_client import download_dump


class MemoryDumper:

    def __init__(self, vm, interval=10, times=5):
        self._vm = vm

        """Socket port didn't close right away when LiME module rmmod.
            It has to use another port to alternate socket port"""
        self._tmp_port = 0
        self._lime_path = Config.get_dump_path(self._vm.arch)
        self._lime_port = int(Config.get_dump_port(self._vm.arch))
        self._lime_format = Config.get_dump_format(self._vm.arch)
        self._save_fmt_path = Config.get_save_dump_path(self._vm.arch, self._vm.name + "_%s")
        check_and_mkdir(self._save_fmt_path)

        self._ipv4 = self._get_ipv4()
        self._mutex = threading.Lock()
        self._timer = RepeatableTimer(interval, self.dump_memory)

        self._remain_times = times
        self._dump_times = times

    @property
    def mutex(self):
        return self._mutex

    @property
    def timer(self):
        return self._timer

    @property
    def vm(self):
        return self._vm

    @property
    def dump_times(self):
        return self._dump_times

    @property
    def remain_times(self):
        return self._remain_times

    @remain_times.setter
    def remain_times(self, nums):
        if nums >= 0:
            self._remain_times = nums

    def _dump_mutex(func):
        """This is a decorator that acquire mutex before running function and
         release after finished"""
        @wraps(func)
        def wrapper(inst, *args, **kwargs):
            inst.mutex.acquire()
            result = 0
            if inst.remain_times:
                inst.timer.start()
                result = func(inst, *args, **kwargs)
                if result == 0:
                    inst.timer.cancel()
                else:
                    inst.remain_times -= 1
            else:
                # init dump status and times
                inst.vm.dump_enabled = False
                inst.remain_times = inst.dump_times

            inst.mutex.release()
            return result
        return wrapper

    def _get_ipv4(self):
        """"""
        child = pexpect.spawn('virsh --connect qemu:///system domifaddr %s' % self._vm.name)
        child.expect(['ipv4', pexpect.TIMEOUT, pexpect.EOF])
        ipv4 = re.search(r'((\d{1,3}.){3}\d{1,3})', child.buffer)
        child.close()
        if not ipv4:
            logging.error('Cannot get ipv4 address in VM %s' % self._vm.name)
            return None
        return ipv4.group(0)

    @staticmethod
    def _read_lines(child):
        out = child.readline()
        while out:
            print out
            out = child.readline()

    @staticmethod
    def _read_buffer(child):
        print "buffer", child.buffer
        print "before", child.before
        print "after", child.after

    @_dump_mutex
    def dump_memory(self):
        """Dump guest VM memory to host"""

        def child_close(c, _return=1):
            c.close()
            return _return

        """Exit if have not getting ipv4 address"""
        if not self._ipv4:
            return 0

        cmd = "virsh --connect qemu:///system console %s" % self._vm.name
        child = pexpect.spawn(cmd, timeout=3)

        index = child.expect([pexpect.TIMEOUT, "failed to get domain", "console session exists", pexpect.EOF], timeout=1)
        if index == 0:
            x = re.search("is \^\]", child.buffer)
            if not x:
                logging.error("Virsh connect to %s timeout!" % self._vm.name)
        elif index == 1:
            logging.error("Failed to get domain %s." % self._vm.name)
        elif index == 2:
            logging.error("Operation failed: Active console session exists for %s." % self._name)
        else:
            logging.error("Virsh connect to %s failed!" % self._vm.name)
        if index:
            return child_close(child, _return=0)

        child.send('\n')

        index = child.expect(["#", "login", pexpect.EOF, pexpect.TIMEOUT])

        if index == 1:
            """ login session """
            child.sendline(self._vm.username)
            child.sendline(self._vm.password)
            child.send('\n')

            index = child.expect(["#", "incorrect", pexpect.EOF, pexpect.TIMEOUT])
            if index == 1:
                logging.error("Login incorrect in %s with %s:%s" % (self._vm.name, self._vm.username, self._vm.password))
            elif index > 1:
                logging.error("Find unknown reason in login getty of %s!" % self._vm.name)
        elif index > 1:
            logging.error("Login failed.")

        if index == 0:
            logging.info("VM %s login successfully!" % self._vm.name)
        else:
            return child_close(child, _return=0)

        insmod_cmd = 'insmod %s "path=tcp:%s format=%s"' % (self._lime_path, self._lime_port + self._tmp_port, self._lime_format)
        logging.debug('insmod lime.. (%s)' % insmod_cmd)
        child.sendline(insmod_cmd)
        time.sleep(1)

        save_path = self._save_fmt_path % time.strftime("%Y%m%d_%H%M%S", time.localtime())

        logging.debug('Download memory dump..')
        download_status = download_dump(save_path, self._ipv4, self._lime_port + self._tmp_port)
        child.send('\n')

        # Increase alternative port number.
        self._tmp_port = self._tmp_port + 1 % 10

        # can't connect to server
        if not download_status:
            return child_close(child, _return=0)

        index = child.expect(["#", pexpect.EOF, pexpect.TIMEOUT])

        if index == 0:
            host = pexpect.spawn("ls -s %s" % save_path)
            hindex = host.expect(["cannot access", "\s%s" % save_path, pexpect.EOF, pexpect.TIMEOUT])

            if hindex == 1:
                size = kb_to_mb(host.before)

                if size != self._vm.ram:
                    logging.error("The saved [%s] mem size %dM is inconsistent with VM ram size %dM." % (self._name, size, self._ram))
                else:
                    logging.info("Save VM %s memory successfully." % self._vm.name)
            else:
                logging.info("Save VM %s memory failed." % self._vm.name)

            host.close()
        else:
            logging.error("VM %s insmod failed." % self._vm.name)

        child.sendline('lsmod')
        index = child.expect(["lime", pexpect.EOF, pexpect.TIMEOUT])

        if index == 0:
            child.sendline('rmmod lime')
            child.sendline('lsmod')
        else:
            logging.error("VM %s have not found lime kernel module." % self._vm.name)

        return child_close(child, _return=1)

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.cancel()
