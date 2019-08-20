import socket
import logging


def download_dump(filepath, host, port):
    s = socket.socket()

    try:
        logging.debug('connecting to server.. (%s:%s)' % (host, port))
        s.connect((host, int(port)))

        logging.debug('file open.. (%s)' % filepath)
        try:
            with open(filepath, 'wb') as f:
                while True:
                    data = s.recv(1024)
                    if not data:
                        break
                    f.write(data)
        except EnvironmentError as e:  # parent of IOError, OSError *and* WindowsError where available
            logging.error('Find some errors when opening file ..', exc_info=e)
            #logging.debug('', exc_info=e)
            return 0

        #s.shutdown(socket.SHUT_WR)
        s.close()
    except socket.error as e:
        logging.error('Find some errors when connecting to server..')
        #logging.debug('', exc_info=e)
        return 0



    return 1
