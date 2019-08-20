import logging
from common.repeat_timer import RepeatableTimer
from common.utils import pause
from common.logger import setup_logger, init_logger
from libvmi import Libvmi, VMIOS


class ProcessChecker:

    def __init__(self, vm_name, callback=None, interval=10):
        self._vm_name = vm_name
        self._callback = callback
        self._init_vmi()

        self.logger = setup_logger(vm_name, vm_name+'/'+vm_name+'.log')
        self._ori_ps_list = self._get_process_list()
        self._ori_ps_set = set(self._ori_ps_list.keys())
        self._timer = RepeatableTimer(interval, self._check_process)

    def _init_vmi(self):
        """ Initialize LibVMI """
        self._vmi = Libvmi(self._vm_name)

        # get ostype
        self._os = self._vmi.get_ostype()

        # init offsets values
        self._tasks_offset = None
        self._name_offset = None
        self._pid_offset = None
        if self._os == VMIOS.LINUX:
            self._tasks_offset = self._vmi.get_offset("linux_tasks")
            self._name_offset = self._vmi.get_offset("linux_name")
            self._pid_offset = self._vmi.get_offset("linux_pid")
        elif self._os == VMIOS.WINDOWS:
            self._tasks_offset = self._vmi.get_offset("win_tasks")
            self._name_offset = self._vmi.get_offset("win_pname")
            self._pid_offset = self._vmi.get_offset("win_pid")
        else:
            self.logger.error("Unknown OS")
            return 0
        return 1

    def _get_process_list(self):
        """
        Get the process list inside the VM
        :return: process list of getting the page successfully or None.
        """
        # pause vm
        with pause(self._vmi):
            # demonstrate name and id accessors
            name = self._vmi.get_name()
            id = self._vmi.get_vmid()

            self.logger.debug("Process listing for VM %s (id: %s)", name, id)
            if self._os == VMIOS.LINUX:
                list_head = self._vmi.translate_ksym2v("init_task")
                list_head += self._tasks_offset
            elif self._os == VMIOS.WINDOWS:
                list_head = self._vmi.read_addr_ksym("PsActiveProcessHead")
            else:
                self.logger.error("Unknown OS")
                return None

            process_list = dict()
            cur_list_entry = list_head
            next_list_entry = self._vmi.read_addr_va(cur_list_entry, 0)

            while True:
                current_process = cur_list_entry - self._tasks_offset
                pid = self._vmi.read_32_va(current_process + self._pid_offset, 0)
                procname = self._vmi.read_str_va(current_process + self._name_offset, 0)
                process_list[pid] = (procname, hex(current_process))

                self.logger.debug("[%s] %s (struct addr:%s)", pid, procname,
                              hex(current_process))
                cur_list_entry = next_list_entry
                next_list_entry = self._vmi.read_addr_va(cur_list_entry, 0)

                if self._os == VMIOS.WINDOWS and next_list_entry == list_head:
                    break
                elif self._os == VMIOS.LINUX and cur_list_entry == list_head:
                    break

            return process_list

    def _check_process(self):
        self._timer.start()

        ps_list = self._get_process_list()
        ps_set = set(ps_list.keys())

        new_ps = ps_set - self._ori_ps_set
        reduce_ps = self._ori_ps_set - ps_set

        if new_ps:
            for pid in new_ps:
                self.logger.warning("detected new process. [%s] %s (struct addr:%s)",
                                    pid, ps_list[pid][0], ps_list[pid][1])

        if reduce_ps:
            for pid in reduce_ps:
                self.logger.warning("detected process leave. [%s] %s (struct addr:%s)",
                                    pid, self._ori_ps_list[pid][0], self._ori_ps_list[pid][1])

        self._ori_ps_list = ps_list
        self._ori_ps_set = ps_set

    def start(self):
        """Start a thread that compares both of origin process list and a new one"""
        self._timer.start()

    def stop(self):
        """stop process checker"""
        self._timer.cancel()
        self._vmi.destroy()


if __name__ == "__main__":
    init_logger()
    vm_name = "vm4"
    checkers = ProcessChecker(vm_name)
    checkers.start()