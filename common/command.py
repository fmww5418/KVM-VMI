import subprocess
from threading import Timer
from common.logger import init_logger
import logging


def kill(process):
    try:
        process.kill()
    except OSError:
        pass  # ignore


def command(cmd, timeout=0):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

    if timeout:
        t = Timer(timeout, kill, [process])
        t.start()

    output, error = process.communicate()

    if timeout:
        process.wait()
        t.cancel()

    if process.returncode != 0:
        try:
            process.terminate()
        except OSError:
            pass  # ignore
        logging.error("Run command failed! (code:%d, erro:%s)\ncmd: [%s]\n%s" %
                      (process.returncode, error, cmd, output))
        return None

    return output


# test
if __name__ == "__main__":
    init_logger()
    outs = command("ping -c 1 8.8.8.8; sleep 6", timeout=3)
    print outs
