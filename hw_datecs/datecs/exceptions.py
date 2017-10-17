""" ESC/POS Exceptions classes """

import os

class Error(Exception):
    """ Base class for ESC/POS errors """
    def __init__(self, msg, status=None):
        Exception.__init__(self)
        self.msg = msg
        self.resultcode = 1
        if status is not None:
            self.resultcode = status

    def __str__(self):
        return self.msg

# Result/Exit codes
# Numbers: 0,1,2,5,10,11,12,14 are reflected in the file field of the file
# 0  = command completed successfully;
# 1  = Communication Error! Verify that the device is in good condition or whether it is working is connected to the computer;
# 2  = Command error. Check for open buon, set clock and correct device settings;
# 3  = The program can not open COM port No;
# 4  = No such device;
# 5  = Wrong command syntax;
# 6  = Non-existent file;
# 7  = Abnormality in the file structure;
# 8  = Please enter your registration key;
# 9  = Please enter all parameters correctly;
# 10 = Undefined error;
# 11 = No paper (fiscal machines only);
# 12 = Fiscal command not allowed (fiscal printers only);
# 14 = The fiscal memory is full;

class CommunicationFault(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 1

    def __str__(self):
        return "Communication Error! Verify that the device is in good condition or whether it is working is connected to the computer."

class CommandFault(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 2

    def __str__(self):
        return "Command error. Check for open buon, set clock and correct device settings."

class CommandWrong(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 5

    def __str__(self):
        return "Wrong command syntax."


class UndefinedFault(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 10

    def __str__(self):
        return "Undefined error"

class PaperFault(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 11

    def __str__(self):
        return "No paper"

class FiscalFault(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 12

    def __str__(self):
        return "Fiscal command not allowed"

class MemoryFull(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 14

    def __str__(self):
        return "The Fiscal memory is full"

class BarcodeTypeError(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 20

    def __str__(self):
        return "No Barcode type is defined"

class BarcodeSizeError(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 30

    def __str__(self):
        return "Barcode size is out of range"

class BarcodeCodeError(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 40

    def __str__(self):
        return "Code was not supplied"

class ImageSizeError(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 50

    def __str__(self):
        return "Image height is longer than 255px and can't be printed"

class TextError(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 60

    def __str__(self):
        return "Text string must be supplied to the text() method"


class CashDrawerError(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 70

    def __str__(self):
        return "Valid pin must be set to send pulse"

class NoStatusError(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 80

    def __str__(self):
        return "Impossible to get status from the printer: " + str(self.msg)

class TicketNotPrinted(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 90

    def __str__(self):
        return "A part of the ticket was not been printed: " + str(self.msg)

class NoDeviceError(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 100

    def __str__(self):
        return str(self.msg)

class HandleDeviceError(Error):
    def __init__(self, msg=""):
        Error.__init__(self, msg)
        self.msg = msg
        self.resultcode = 110

    def __str__(self):
        return str(self.msg)
