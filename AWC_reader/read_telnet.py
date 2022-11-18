#!/usr/bin/env python3

# import subprocess
import asyncio
import datetime
import logging
import telnetlib
import time
from logging.handlers import TimedRotatingFileHandler

# from argparse import ArgumentParser
import psutil
import telnetlib3
from path import Path


IPs = dict(AWC1='10.2.2.201', AWC2='10.2.2.205')
FOLDER = r'G:\.shortcut-targets-by-id\1zJg6xXMQtwsL4z7K86PE8FS6FspMhFec\04_PROJETS\21_Deux-Acren\13_EXECUTION\Réception\Tests préalables\DEIF-exports'

FILE_PATTERN = "{date}_AWC{awc}.log"
DATEFORMAT = '%Y%m%d_%H%M'

TIMELOGGER = dict(when='H', interval=1, date_fmt='%Y%m%d_%H%M')

test = True
if test:
    FOLDER = Path(r'C:\Users\MLevy\Documents\2Acren')
    FOLDER /= 'tmp'
    TIMELOGGER = dict(when='S', interval=20)
    DATEFORMAT = '%Y%m%d_%H%M%S'

class TimedRotatingFileHandlerWithHeader(TimedRotatingFileHandler):
    def __init__(
        self, logfile:Path, header='', date_fmt=DATEFORMAT, **kwargs
    ):
        self._start_time = datetime.datetime.utcnow()
        self._datefmt = date_fmt

        super(TimedRotatingFileHandlerWithHeader, self).__init__(
            logfile, utc=True, **kwargs
        )

        self._header = header
        self._write_header(self.baseFilename)

    @property
    def baseFilename(self):
        return self.namer()

    @property
    def rawFilename(self):
        return self._baseFilename

    @baseFilename.setter
    def baseFilename(self, name):
        self._baseFilename = Path(name)
        self._folder = self._baseFilename.parent
        self._basename = self._baseFilename.basename()

    def _write_header(self, file):
        if self._header:
            file.write_lines([self._header], append=True)

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, header):
        self._header = header

    def namer(self, *args):
        date_str = self._start_time.strftime(self._datefmt)
        name = self._folder / self._basename.format(date=date_str)
        return name

    def rotation_filename(self, default_name):
        """
        Overwrite default behaviour called in doRollover
        :param default_name: unused, for compatibility only
        :return: filename of next file for rotating logging
        """
        self._start_time = datetime.datetime.utcnow()
        return self.namer()


    def rotate(self, source, dest):
        """
        Overwriting rotate method made useless because baseFilename already changed.
        We simply need to add a header
        :param source: The source filename. This is normally the base
                       filename, e.g. 'test.log'
        :param dest:   The destination filename. This is normally
                       what the source is rotated to, e.g. 'test.log.1'.
        """
        print(f"New file created for logger: {self.baseFilename}")
        self._write_header(self.baseFilename)


def get_ip(awc):
    return IPs[f"AWC{awc}"]


def search_proc(name=''):
    return [p for p in psutil.process_iter() if name in p.name().lower()]


def search_telnet_reader(awc=1):
    ip = get_ip(awc)
    telnets = [p for p in search_proc('telnet') if ip in p.cmdline()]
    if telnets:
        return telnets[0]


def create_data_logger(file_basename, header='', level = logging.DEBUG):
    logger = logging.getLogger(file_basename)
    # logger.basicConfig(filename=filename, encoding='utf-8', level=logging.DEBUG)
    handler = TimedRotatingFileHandlerWithHeader(
        file_basename,
        **TIMELOGGER,
        # atTime='midnight',
        header=header,
    )
    handler.setFormatter(logging.Formatter('%(message)s'))

    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


async def lauch_telnet(awc=1, folder=None):
    """Launch a telnet reading command on awc `awc`to file `file`"""
    if not folder:
        folder = Path(FOLDER)
    filename_pattern = folder / FILE_PATTERN.format(awc=awc, date='{date}')

    use_telnetlib3 = False
    if use_telnetlib3:
        tnet_io = telnetlib3.open_connection(get_ip(awc), port=23, cols=300, log=None)
        # r,w =asyncio.run(tnet_io)
        # while True:
        #     readline = asyncio.create_task(r.readline())
        #     await readline
        #     logger.info( readline.result().rstrip())

    else:
        retry_delay = 0
        while True:
            try:
                with telnetlib.Telnet(host=get_ip(awc), port=23) as tnet:
                    header = tnet.read_until(b'\r\n').decode().rstrip()
                    data_logger = create_data_logger(filename_pattern, header=header)
                    for h in data_logger.handlers:
                        print(
                            f"Logging AWC {awc} in file \n{h.baseFilename}"


                    retry_delay = 0
                    while True:
                        line = tnet.read_until(b'\r\n').decode().rstrip()
                        data_logger.info(line)
                        await asyncio.sleep(0)
            except (
                ConnectionResetError,
                ConnectionRefusedError,
                TimeoutError,
                EOFError,
            ) as err:
                print(f"Connection on AWC {awc} failed: {err}")
                print(f"-> Starting again in {retry_delay} seconds.")
                await asyncio.sleep(retry_delay)
                retry_delay = min((retry_delay * 2 or 0.5), 60)


async def call_logs():
    loggers = dict()
    for awc in range(1, 3):
        loggers[awc] = lauch_telnet(awc)
    await asyncio.gather(*loggers.values())

if __name__ == '__main__':
    asyncio.run(call_logs())
