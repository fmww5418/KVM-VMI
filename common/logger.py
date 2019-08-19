import os
import sys
import logging
import logging.config
import threading
import yaml
from utils import check_and_mkdir

from config import Config, EnvType, LogLevel

formatter = ''


class SingleLevelFilter(logging.Filter):

    def __init__(self, passlevel, accept, name=''):
        self.passlevel = passlevel
        self.accept = accept

        return super(SingleLevelFilter, self).__init__(name)

    def filter(self, record):
        for i, lv in enumerate(self.passlevel):
            try:
                if record.levelno == lv:
                    return self.accept[i]
            except IndexError:
                return False
        return False

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
                Config.get_value(EnvType.LOG_PATH.value) + log_file
    dir_path, file_name = os.path.split(full_path)

    check_and_mkdir(dir_path)

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

    """
    h1 = logging.StreamHandler(sys.stdout)
    f1 = SingleLevelFilter([logging.INFO, logging.DEBUG], [False, True])
    h1.addFilter(f1)
    rootLogger = logging.getLogger()
    #rootLogger.addHandler(h1)
    logger = logging.getLogger("debug.logger")
    logger.setLevel(logging.DEBUG)
    logger.debug("A DEBUG message")
    logger.info("An INFO message")
    logger.warning("A WARNING message")
    logger.error("An ERROR message")
    logger.critical("A CRITICAL message")
    """
    # first file logger
    root = setup_logger('root', '/abc/root.log')

    logger = setup_logger('first_logger', '/abc/first_logfile.log')
    logging.getLogger('first_logger').addHandler(root)

    root.info('This is root')
    logger.info('This is logger')

    logging.debug("aaa")
