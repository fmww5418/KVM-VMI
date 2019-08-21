from contextlib import contextmanager
import logging
import os
import math


def check_and_mkdir(path):
    """ Make Directory if a specific path does not exist """
    dir_path, file_name = os.path.split(path)
    if not os.path.isdir(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as exc:
            logging.error('Create folder failed. (%s) %s' % (dir_path, exc.message))
            raise

@contextmanager
def pause(vmi):
    vmi.pause_vm()
    try:
        yield
    finally:
        vmi.resume_vm()


def dtb_to_pname(vmi, dtb):
    tasks_off = vmi.get_offset('win_tasks')
    pdb_off = vmi.get_offset('win_pdbase')
    name_off = vmi.get_offset('win_pname')
    ps_head = vmi.translate_ksym2v('PsActiveProcessHead')
    flink = vmi.read_addr_ksym('PsActiveProcessHead')

    while flink != ps_head:
        start_proc = flink - tasks_off
        value = vmi.read_addr_va(start_proc + pdb_off, 0)
        if value == dtb:
            return vmi.read_str_va(start_proc + name_off, 0)
        flink = vmi.read_addr_va(flink, 0)
    return None


def kb_to_mb(data):
    """ KB(2^10) convert to MB(2^20) """
    return int(math.ceil(float(data) / pow(2, 10)))


class Const(object):

    class ConstError(TypeError):
        pass

    class ConstCaseError(ConstError):
        pass

    def __setattr__(self, name, value):
        if self.__dict__.has_key(name):
            raise self.ConstError, "can't change const.%s" % name
        if not name.isupper():
            raise self.ConstCaseError, "const name '%s' is not all uppercase" % name

        self.__dict__[name] = value


