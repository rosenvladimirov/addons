#!/usr/bin/python

import logging
import usb.core
import usb.util
import serial
import socket
import codecs
from tempfile import gettempdir

from datecs import *
from exceptions import *
from time import sleep

_logger = logging.getLogger(__name__)

class Usb(Datecs):
    """ Define USB printer """

    def __init__(self, idVendor, idProduct, interface=0, in_ep=0x82, out_ep=0x01):
        """
        @param idVendor  : Vendor ID
        @param idProduct : Product ID
        @param interface : USB device interface
        @param in_ep     : Input end point
        @param out_ep    : Output end point
        """
        self.errorText = ""

        self.idVendor  = idVendor
        self.idProduct = idProduct
        self.interface = interface
        self.in_ep     = in_ep
        self.out_ep    = out_ep
        self.open()

    def open(self):
        """ Search device on USB tree and set is as datecs device """
        self.device = usb.core.find(idVendor=self.idVendor, idProduct=self.idProduct)
        if self.device is None:
            raise NoDeviceError()
        try:
            if self.device.is_kernel_driver_active(self.interface):
                self.device.detach_kernel_driver(self.interface) 
            self.device.set_configuration()
            usb.util.claim_interface(self.device, self.interface)
        except usb.core.USBError as e:
            raise HandleDeviceError(e)

    def close(self):
        i = 0
        while True:
            try:
                if not self.device.is_kernel_driver_active(self.interface):
                    usb.util.release_interface(self.device, self.interface)
                    self.device.attach_kernel_driver(self.interface)
                    usb.util.dispose_resources(self.device)
                else:
                    self.device = None
                    return True
            except usb.core.USBError as e:
                i += 1
                if i > 10:
                    return False
            sleep(0.1)

    def _raw(self, msg):
        """ Print any command sent in raw format """
        if len(msg) != self.device.write(self.out_ep, msg, self.interface):
            self.device.write(self.out_ep, self.errorText, self.interface)
            raise TicketNotPrinted()

    def __del__(self):
        """ Release USB interface """
        if self.device:
            self.close()
        self.device = None

class Serial(Datecs):
    """ Define Serial printer """

    def __init__(self, devfile="/dev/ttyS0", baudrate=9600, bytesize=8, timeout=1):
        """
        @param devfile  : Device file under dev filesystem
        @param baudrate : Baud rate for serial transmission
        @param bytesize : Serial buffer size
        @param timeout  : Read/Write timeout
        """
        self.devfile  = devfile
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.timeout  = timeout
        self.open()

    def open(self):
        """ Setup serial port and set is as datecs device """
        self.device = serial.Serial(port=self.devfile, baudrate=self.baudrate, bytesize=self.bytesize, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=self.timeout, dsrdtr=True)

        if self.device is not None:
            print "Serial printer enabled"
        else:
            print "Unable to open serial printer on: %s" % self.devfile

    def _raw(self, msg):
        """ Print any command sent in raw format """
        self.device.write(msg)

    def __del__(self):
        """ Close Serial interface """
        if self.device is not None:
            self.device.close()

class Network(Datecs):
    """ Define Network printer """

    def __init__(self,host,port=9100):
        """
        @param host : Printer's hostname or IP address
        @param port : Port to write to
        """
        self.host = host
        self.port = port
        self.open()

    def open(self):
        """ Open TCP socket and set it as datecs device """
        self.device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.device.connect((self.host, self.port))

        if self.device is None:
            print "Could not open socket for %s" % self.host

    def _raw(self, msg):
        self.device.send(msg)

    def __del__(self):
        """ Close TCP connection """
        self.device.close()

class FPrint(Datecs):
    """ Define FPrint ext driver """
    def __init__(self, sq):
        """
        @param fname : FPrint fname to write
        """
        self.path = os.path.join(gettempdir(), "fprint", "")
        self.filename  = self.path + "receipt.inp"
        self.errorname = self.path + "err.ret"
        self.device = False
        self.locked   = False
        self.driver = Datecs()
        self.driver.set_sequence(sq)

    def set_sequence(self, sq):
        self.driver.set_sequence(sq)

    def get_sequence(self, sq):
        return self.driver.get_sequence()

    def get_filename(self):
        return self.filename

    def open(self):
        """ Open File and set it as datecs device """
        if not self.device:
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            #while os.path.isfile(self.filename):
            #    print "FPrint is not remove file. Wait it"
            self.device = codecs.open(self.filename, "w", "utf-8")
            self.locked = True
            _logger.info("Driver: %s:%s:%s" % (self.driver, self.filename, self.device))
        if self.device is None:
            print "Could not open file for %s" % self.filename

    def _raw(self, lines):
        if self.locked:
            if isinstance(lines, (str, unicode)):
                self.device.write(lines+'\n')
            elif isinstance(lines, list):
                self.device.writelines(lines)

    def _flush(self):
        errors = []
        self.open()
        if self.locked:
            self.device.writelines(self.lines)

        if self.device and self.locked:
            self.device.close()
            self.device = False
            self.locked = False

        if not self.device:
            while os.path.isfile(self.filename):
                print "FPrint nu a terminat tiparirea fisierului"
            while self.locked:
                print "Wait to finish last operations"
            self.device = open(self.filename, "r")
            err = self.device.readlines()
            self.device.close()
            self.device = False
        if err:
            error.append(err.split(";")[0].split(",")[4])
        return errors

    def __del__(self):
        """ Close file and flush """
        ret = []
        ret = self._flush()
        for error in ret:
            if error == 'Ok':
                continue
            elif error == 'Sd':
                raise CommunicationFault()
                break

        if self.device:
            self.device.close()
        return ret

    def close(self):
        if self.device:
            ret = self.device.close()
            self.device = False
            return ret
