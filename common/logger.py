import os
import sys
import logging
import logging.config
import threading
import yaml
from utils import check_and_mkdir

from config import Config, EnvType, LogLevel

formatter = ''

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

#These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': YELLOW,
    'ERROR': RED
}


def formatter_message(message, use_color=True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color

        return super(ColoredFormatter, self).format(record)


class ColoredLogger(logging.Logger):
    """Custom logger class with multiple destinations"""
    #FORMAT = "[$BOLD%(name)-20s$RESET][%(levelname)-18s]  %(message)s ($BOLD%(filename)s$RESET:%(lineno)d)"
    COLOR_FORMAT = formatter_message(formatter, True)

    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.DEBUG)

        color_formatter = ColoredFormatter(self.COLOR_FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(console)
        return


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

    check_and_mkdir(full_path)

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

        # set logger class for colored level name
        #logging.setLoggerClass(ColoredLogger)

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
    #root = setup_logger('root', '/abc/root.log', logging.DEBUG)

    logger = setup_logger('first_logger', '/abc/first_logfile.log')
    #logging.getLogger('first_logger').addHandler(root)

    #root.info('This is root')
    logging.debug("tat")
    logger.error('This is logger')
    #root.debug('test')

    #root.warning("aaa")
