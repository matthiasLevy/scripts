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
# FILE = "%Y%m%d_%H%M%S-AWC{awc}.log"
FILE = "AWC{awc}_raw.log"
FILE_HEADER = "AWC{awc}.log"

TIMELOGGER = dict(when='H', interval=1, date_fmt='%Y%m%d_%H%M')

test = False
if test:
    FOLDER = Path(r'C:\Users\MLevy\Documents\2Acren')
    FOLDER /= 'tmp'
    TIMELOGGER = dict(when='S', interval=20, date_fmt='%Y%m%d_%H%M%S')

class TimedRotatingFileHandlerWithHeader(TimedRotatingFileHandler):
    def __init__(
        self, logfile, header='', logger=None, date_fmt='%Y%m%d_%H%M', **kwargs
    ):
        self._start_time = datetime.datetime.utcnow()
        self._datefmt = date_fmt

        super(TimedRotatingFileHandlerWithHeader, self).__init__(
            logfile, utc=True, **kwargs
        )
        # logging.handlers.TimedRotatingFileHandler.__init__(logfile, when, interval)

        self._header = header
        self._loggger = logger
        logger.addHandler(self)

        self._write_header()

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

    def _write_header(self):
        file = self._loggger.handlers[0].baseFilename
        # print(f"Writing header in {file}")
        if self._loggger is not None and self._header != "":
            self._loggger.info(self._header)
            # print("-> OK")

    def doRollover(self):
        # super(TimedRotatingFileHandler_withheader, self).doRollover()
        # logging.handlers.TimedRotatingFileHandler.doRollover(self)

        # Correcting original Rollover for naming:
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)

        # Changes below
        self._start_time = datetime.datetime.utcnow()
        if Path(self.baseFilename).exists():
            Path(self.baseFilename).remove()

        # End of changes

        if not self.delay:
            self.stream = self._open()
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if (
                    not dstNow
                ):  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt

        print(f"New file created for logger: {self.baseFilename}")
        self._write_header()

        # self._start_time = datetime.datetime.utcnow()

    def setHeader(self, header):
        self._header = header

    def configureHeaderWriter(self, log, header=None):
        self._header = header or self._header
        self._loggger = log

    def namer(self, *args):
        date_str = self._start_time.strftime(self._datefmt)
        name = self._folder / (date_str + '_' + self._basename)
        return name

    #
    # def rotate(self, source, dest):
    #     """
    #     When rotating, rotate the current log.
    #
    #     The default implementation calls the 'rotator' attribute of the
    #     handler, if it's callable, passing the source and dest arguments to
    #     it. If the attribute isn't callable (the default is None), the source
    #     is simply renamed to the destination.
    #
    #     :param source: The source filename. This is normally the base
    #                    filename, e.g. 'test.log'
    #     :param dest:   The destination filename. This is normally
    #                    what the source is rotated to, e.g. 'test.log.1'.
    #     """
    #     import os
    #     if not callable(self.rotator):
    #         # Issue 18940: A file may not have been created if delay is True.
    #         if os.path.exists(source):
    #             print(f"Renaming {source} in {dest}")
    #             Path(source).move(dest)
    #     else:
    #         self.rotator(source, dest)



def get_ip(awc):
    return IPs[f"AWC{awc}"]


def search_proc(name=''):
    return [p for p in psutil.process_iter() if name in p.name().lower()]


def search_telnet_reader(awc=1):
    ip = get_ip(awc)
    telnets = [p for p in search_proc('telnet') if ip in p.cmdline()]
    if telnets:
        return telnets[0]


# @asyncio.coroutine
# def shell(reader, writer):
#     while True:
#         # read stream until '?' mark is found
#         outp = yield from reader.read(1024)
#         if not outp:
#             # End of File
#             break
#         elif '?' in outp:
#             # reply all questions with 'y'.
#             writer.write('y')
#
#         # display all server output
#         print(outp, flush=True)
#
#     # EOF
#     print()


def get_logger(file, ts=False):
    name = 'AWC_raw' + ('no_ts' if not ts else 'ts')
    logger = logging.getLogger(file)
    # logger.basicConfig(filename=filename, encoding='utf-8', level=logging.DEBUG)
    handler = logging.handlers.TimedRotatingFileHandler(
        file, when='H', atTime='midnight'
    )
    if ts:
        format = '%(asctime)s;%(message)s'
        formatter = logging.Formatter(format, datefmt='%m/%d/%Y %H:%M:%S.')
    else:
        format = '%(message)s'
        formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


def get_logger_header(file, header=''):
    name = 'AWC_'
    logger = logging.getLogger(file)
    logger.setLevel(logging.DEBUG)
    # logger.basicConfig(filename=filename, encoding='utf-8', level=logging.DEBUG)
    handler = TimedRotatingFileHandlerWithHeader(
        file,
        **TIMELOGGER,
        # atTime='midnight',
        header=header,
        logger=logger,
    )
    # handler = TimedRotatingFileHandler_withheader(file, when='S', interval=15, date_fmt='%Y%m%d_%H%M%S',
    #                                               atTime='midnight', header=header, logger=logger)

    handler.setFormatter(logging.Formatter('%(message)s'))
    # while logger.hasHandlers():
    #     logger.removeHandler(logger.handlers[0])
    return logger


async def lauch_telnet(awc=1, folder=None):
    """lauch a telet reading command on awc `awc`to file `file`"""
    if not folder:
        folder = Path(FOLDER)
    filename = datetime.datetime.now().strftime(FILE.format(awc=awc))
    file = folder / filename
    file_header = folder / FILE_HEADER.format(awc=awc)

    # logger = get_logger(file, ts= False)
    # print(f"Logging AWC {awc} in {file}")

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
                    logger_header = get_logger_header(file_header, header=header)
                    for h in logger_header.handlers:
                        print(
                            f"Logging AWC {awc} in file \n{h.baseFilename}"
                            # + f"with pattern {h.rawFilename}:"
                        )
                    # logger.info(header)

                    retry_delay = 0
                    while True:
                        line = tnet.read_until(b'\r\n').decode().rstrip()
                        # logger.info(line)
                        logger_header.info(line)
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
        # asyncio.create_task(loggers[awc])
    await asyncio.gather(*loggers.values())


asyncio.run(call_logs())
