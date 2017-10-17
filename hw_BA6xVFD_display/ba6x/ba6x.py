#!/usr/bin/python

import logging
import usb.core
import usb.util
import serial
import socket
import codecs
import time

from . import vfdpos
from exceptions import *

_logger = logging.getLogger(__name__)

class Display():
    """ Define USB display """

    def __init__(self, idProduct):
        """
        @param idProduct : Product ID

        """
        self.errorText = ""

        self.idProduct = idProduct
        self.open()

    def open(self):
        self.device = vfdpos.vfd_pos(self.idProduct)
        if self.device is None:
            raise NoDeviceError()

    def close(self):
        self.device.clear()

    def status(self):
        return self.device.status()

    def set_charset(self, charset):
        self.device.set_charset(charset)

    def cursor(self, line=0, column=0):
        self.device.poscur(line, column)

    def clear(self):
        self.device.clear()

    def _raw(self, msg):
        self.device.write_msg(msg)

    def __del__(self):
        """ Release USB interface """
        if self.device:
            self.close()
        self.device = None

#if __name__ == '__main__':
#    present_time = time.localtime()
#    dev = Display(0x200)
#    date = time.strftime("%a %d %b %Y", present_time).center(20)
#    hour = time.strftime("%H:%M", present_time).center(20)
#    dev.cursor(0,0)
#    dev._raw(date)
#    dev.cursor(2,0)
#    dev._raw(hour)
