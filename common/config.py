#from Configparser import configparser, NoOptionError, NoSectionError
try:
    import configparser
except:
    from six.moves import configparser

from enum import Enum
import os
import logging

DEBUG = True


class VMArch(Enum):
    x86_64 = 'x86_64'
    x86 = 'i386'


class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 4
    ERROR = 8
    CRITICAL = 16
    ALL = 31


class EnvType(Enum):
    SECTION = 'installation'
    PREFIX = 'root'
    LOG_PATH = 'log_path'


class x86_64(Enum):
    SECTION = 'x86_64'
    PATH = 'x86_64_path'
    KERNEL = 'kernel_name'
    SRC_DISK = 'src_disk_name'
    RAM_SIZE = 'ram'
    USERNAME = 'username'
    PASSWORD = 'password'
    LIME_FORMAT = 'lime_format'
    LIME_PATH = 'lime_module'
    LINE_PORT = 'lime_port'


class Config:
    __conf = {
        EnvType.SECTION.value: {
            EnvType.PREFIX.value: '/',
            EnvType.LOG_PATH.value: 'log/'
        },
        x86_64.SECTION.value: {
            x86_64.PATH.value: 'x86_64',
            x86_64.KERNEL.value: 'bzImage',
            x86_64.SRC_DISK.value: 'rootfs.ext2',
            x86_64.RAM_SIZE.value: '128',
            x86_64.USERNAME.value: 'root',
            x86_64.PASSWORD.value: 'root',
            x86_64.LIME_PATH.value: '/lib/libcpp.so',
            x86_64.LINE_PORT.value: '4444',
            x86_64.LIME_FORMAT.value: 'lime',

        }
    }


    @staticmethod
    def init_config(file_path):
        Config.cfg = configparser.RawConfigParser()
        Config.cfg.read(file_path)

        for section, v in Config.__conf.items():
            for name, default in v.items():
                Config.__conf[section][name] = Config.get_with_default(section, name, default)

        logging.debug("config load successfully!", Config.__conf)

    @staticmethod
    def get_with_default(section, name, default=None):
        try:
            if default is not None:
                if isinstance(default, bool):
                    return Config.cfg.getboolean(section, name)
                elif isinstance(default, float):
                    return Config.cfg.getfloat(section, name)
                elif isinstance(default, int):
                    return Config.cfg.getint(section, name)
                elif isinstance(default, str):
                    return Config.cfg.get(section, name)

        except (configparser.NoSectionError, configparser.NoOptionError):
            logging.error("Can't get config. (SECTION: %s, NAME: %s)\n" % (section, name))
            if DEBUG:
                print("Can't get config. (SECTION: %s, NAME: %s)\n" % (section, name))
            if default is None:
                raise
            return default

    @staticmethod
    def get_value(name, section=None):
        """Return the value of configuration name"""

        if section is not None and section in Config.__conf:
            if name in Config.__conf[section]:
                return Config.__conf[section][name]

        for s, v in Config.__conf.items():
            if name in v:
                return Config.__conf[s][name]

        return None

    @staticmethod
    def get_dump_port(arch):
        if arch == VMArch.x86_64:
            return Config.get_value(x86_64.LINE_PORT.value)

    @staticmethod
    def get_dump_format(arch):
        if arch == VMArch.x86_64:
            return Config.get_value(x86_64.LIME_FORMAT.value)

    @staticmethod
    def get_dump_path(arch):
        if arch == VMArch.x86_64:
            return Config.get_value(x86_64.LIME_PATH.value)

    @staticmethod
    def get_save_dump_path(arch, name):
        if arch == VMArch.x86_64:
            disk_path = os.path.join(Config.get_value(EnvType.PREFIX.value), "dump/",
                                     Config.get_value(x86_64.PATH.value, x86_64.SECTION.value),
                                     "%s.%s" % (name, Config.get_value(x86_64.LIME_FORMAT.value)))

        return disk_path

    @staticmethod
    def get_src_disk_path(arch):
        if arch == VMArch.x86_64:
            disk_path = os.path.join(Config.get_value(EnvType.PREFIX.value), "image/",
                                     Config.get_value(x86_64.PATH.value, x86_64.SECTION.value),
                                     Config.get_value(x86_64.SRC_DISK.value))

        return disk_path

    @staticmethod
    def get_disk_path(arch, disk_name):
        if arch == VMArch.x86_64:
            disk_path = os.path.join(Config.get_value(EnvType.PREFIX.value), "image/",
                                     Config.get_value(x86_64.PATH.value, x86_64.SECTION.value),
                                     disk_name+os.path.splitext(Config.get_value(x86_64.SRC_DISK.value))[1])

        return disk_path

    @staticmethod
    def get_kernel_path(arch):
        if arch == VMArch.x86_64:
            kernel_path = os.path.join(Config.get_value(EnvType.PREFIX.value), "image/",
                                       Config.get_value(x86_64.PATH.value, x86_64.SECTION.value),
                                       Config.get_value(x86_64.KERNEL.value))

        return kernel_path

    @staticmethod
    def get_ram_size(arch):
        if arch == VMArch.x86_64:
            ram = Config.get_value(x86_64.RAM_SIZE.value, x86_64.SECTION.value)

        return ram


Config.init_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini'))
print Config.get_value('x86_64_path')