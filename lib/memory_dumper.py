import pexpect
import logging
import re
import time
import math
from common.config import Config, x86_64, EnvType, VMArch
from common.logger import setup_logger, init_logger
from common.command import command
from common.utils import check_and_mkdir


class MemoryDumper:

    def __init__(self, vm_name, username, password, arch):
        self._name = vm_name
        self._username = username
        self._password = password
        self._arch = arch

        self._lime_path = Config.get_dump_path(self._arch)
        self._lime_port = Config.get_dump_port(self._arch)
        self._lime_format = Config.get_dump_format(self._arch)
        self._save_path = Config.get_save_dump_path(self._arch, self._name)
        check_and_mkdir(self._save_path)

        self._ipv4 = self._get_ipv4()


    def _get_ipv4(self):
        child = pexpect.spawn('virsh --connect qemu:///system domifaddr %s' % self._name)
        child.expect(['ipv4', pexpect.TIMEOUT, pexpect.EOF])
        ipv4 = re.search(r'((\d{1,3}.){3}\d{1,3})', child.buffer)
        child.close()
        return ipv4.group(0)

    def _readlines(self, child):
        out = child.readline()
        while out:
            print out
            out = child.readline()

    def dump_memory(self):
        cmd = "virsh --connect qemu:///system console %s" % self._name
        child = pexpect.spawn(cmd)

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
            return

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
            return

        insmod_cmd = 'insmod %s "path=tcp:%s format=%s"' % (self._lime_path, self._lime_port, self._lime_format)
        logging.debug('insmod lime.. (%s)' % insmod_cmd)
        child.sendline(insmod_cmd)
        time.sleep(2)

        nc_cmd = "nc %s %s > %s" % (self._ipv4, self._lime_port, self._save_path)
        logging.debug('nc .. (%s)' % nc_cmd)
        command(nc_cmd, timeout=7, ignore=True)
        child.send('\n')
        index = child.expect(["#", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            host = pexpect.spawn("ls -s %s" % self._save_path)
            hindex = host.expect([self._save_path, pexpect.EOF, pexpect.TIMEOUT])

            if hindex == 0:
                p = pow(2, 10)
                size = int(math.ceil(float(host.before)/p))
                ram = int(Config.get_value(x86_64.RAM_SIZE.value))

                if size != ram:
                    logging.error("The saved [%s] mem size %dM is inconsistent with VM ram size %dM." % (self._name, size, ram))
                else:
                    logging.info("Save VM %s memory successfully." % self._name)
            else:
                logging.info("Save VM %s memory failed." % self._name)

            host.close()
        else:
            logging.error("VM %s insmod failed." % self._name)

        child.sendline('lsmod')
        index = child.expect(["lime", pexpect.EOF, pexpect.TIMEOUT], timeout=1)
        if index == 0:
            child.sendline('rmmod lime')
        else:
            logging.error("VM %s have not found lime kernel module." % self._name)

        child.close()


if __name__ == "__main__":
    init_logger()
    session_manager = MemoryDumper("vm2", Config.get_value(x86_64.USERNAME.value), Config.get_value(x86_64.PASSWORD.value), VMArch.x86_64)
    session_manager.dump_memory()
