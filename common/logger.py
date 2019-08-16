import os
import sys
import logging
import logging.config
import threading
import yaml

from common.config import Config, EnvType, LogType, LogLevel

formatter = ''


class MyLogger(logging.Logger):

    def __init__(self, name, level=logging.NOTSET):
        self._level = 0
        self._count = 0
        self._countLock = threading.Lock()

        return super(MyLogger, self).__init__(name, level)

    def extraSetLevel(self, level):
        """
        .DEBUG    : 1
        .INFO     : 2
        .WARNING  : 4
        .ERROR    : 8
        .CRITICAL : 16

        :param level: It's a mask bit that decide to what level to print
        :return: level
        """
        self._level = level
        return self._level

    def debug(self, msg, *args, **kwargs):
        print(Config.get_value(LogType.LOG_DEBUG.value))
        if self._level & LogLevel.DEBUG.value:
            return super(MyLogger, self)._log(logging.DEBUG, msg, args, **kwargs)

    def info(self, msg, *args, **kwargs):
        if self._level & LogLevel.INFO.value:
            print(msg)
            return super(MyLogger, self)._log(logging.INFO, msg, args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        if self._level & LogLevel.WARNING.value:
            return super(MyLogger, self)._log(logging.WARNING, msg, args, **kwargs)

    def error(self, msg, *args, **kwargs):
        if self._level & LogLevel.ERROR.value:
            return super(MyLogger, self)._log(logging.ERROR, msg, args, **kwargs)


def setup_logger(name, log_file, level=logging.INFO):
    """Function setup as many loggers as you want

    level arguments:
      (The log level less than setting level will be ignored)

    .NOTSET   : 0
    .DEBUG    : 10
    .INFO     : 20
    .WARNING  : 30
    .ERROR    : 40
    .CRITICAL : 50
    """

    full_path = Config.get_value(EnvType.PREFIX.value) +\
                Config.get_value(LogType.LOG_PATH.value) + log_file
    dir_path, file_name = os.path.split(full_path)

    if not os.path.isdir(dir_path):
        try:
            os.mkdir(dir_path)
        except OSError as exc:
            logging.error('Create folder failed. (%s)' % dir_path)
            raise

    handler = logging.FileHandler(full_path)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def init_logger():
    global formatter
    # read formatter's format

    path = os.path.join(Config.get_value(EnvType.PREFIX.value), 'logging.yml')
    logging.debug("Read logging.yml .. (%s)", path)

    with open(path, 'r') as f_conf:
        dict_conf = yaml.safe_load(f_conf.read())

        # read default formatter
        formatter = logging.Formatter(dict_conf['formatters']['default']['format'])
        # set log location as abstract path
        for k, v in dict_conf['handlers'].items():
            if 'filename' in v:
                dict_conf['handlers'][k]['filename'] = \
                    os.path.join(Config.get_value(EnvType.PREFIX.value), dict_conf['handlers'][k]['filename'])

        logging.config.dictConfig(dict_conf)

    # set custom class for logger
    #logging.setLoggerClass(MyLogger)


# test
if __name__ == "__main__":
    init_logger()

    # first file logger
    root = setup_logger('root', '/abc/root.log')

    logger = setup_logger('first_logger', '/abc/first_logfile.log')
    logging.getLogger('first_logger').addHandler(root)

    root.info('This is root')
    logger.info('This is logger')

    logging.debug("aaa")
