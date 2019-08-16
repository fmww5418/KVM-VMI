#from Configparser import configparser, NoOptionError, NoSectionError
try:
    import configparser
except:
    from six.moves import configparser

from enum import Enum
import os

DEBUG = True


class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 4
    ERROR = 8
    CRITICAL = 16
    ALL = 31

class LogType(Enum):
    LOG_PATH = 'log_path'
    LOG_INFO = 'log_infos'
    LOG_DEBUG = 'log_debugs'
    LOG_ERROR = 'log_errors'
    LOG_WARNING = 'log_warnings'

class EnvType(Enum):
    PREFIX = 'prefix'


class Config:

    __conf = {
        'installation': {
            EnvType.PREFIX.value: '/'
        },
        'log': {
            LogType.LOG_PATH.value: 'log/',
            LogType.LOG_INFO.value: False,
            LogType.LOG_DEBUG.value: False,
            LogType.LOG_ERROR.value: False,
            LogType.LOG_WARNING.value: False,
        }
    }

    @staticmethod
    def init_config(file_path):
        Config.cfg = configparser.RawConfigParser()
        Config.cfg.read(file_path)

        for section, v in Config.__conf.items():
            for name, default in v.items():
                Config.__conf[section][name] = Config.get_with_default(section, name, default)

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
            if DEBUG:
                print("Can't get config. (SECTION: %s, NAME: %s)\n" % (section, name))
            if default is None:
                raise
            return default

    @staticmethod
    def get_value(name, section=None):
        """Return the value of configuration name"""

        for s, v in Config.__conf.items():
            if name in v:
                return Config.__conf[s][name]

        if section is not None and section in Config.__conf:
            if name in Config.__conf[section]:
                return Config.__conf[section][name]

        return None


Config.init_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini'))
