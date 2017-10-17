# -*- coding: utf-8 -*-
import commands
import logging
import simplejson
import os
import os.path
import io
import base64
import openerp
import time
import random
import math
import md5
import openerp.addons.hw_proxy.controllers.main as hw_proxy
import pickle
import re
import subprocess
import traceback
from openerp.tools import float_is_zero

from .. datecs import *
from .. datecs.exceptions import *
from .. datecs.printer import Usb
from .. datecs.printer import FPrint
from .. datecs.printer import Serial
from .. datecs.printer import Network

#    datecs = printer = None

from threading import Thread, Lock
from Queue import Queue, Empty

try:
    import usb.core
except ImportError:
    usb = None

from PIL import Image

from openerp import http
from openerp.http import request
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

# workaround https://bugs.launchpad.net/openobject-server/+bug/947231
# related to http://bugs.python.org/issue7980
from datetime import datetime
datetime.strptime('2012-01-01', '%Y-%m-%d')
driver_name = 'escpos'

class DatecsDriver(Thread):
    def __init__(self):
        #_logger.info("Datecs init")
        Thread.__init__(self)
        self.setDaemon(True)
        self.queue = Queue()
        self.lock  = Lock()
        #self.join(1)  # give it some time
        self.status = {'status':'connecting', 'messages':[]}
        self.sequence = 0
        self.holdDevice = False

    def connected_usb_devices(self):
        connected = []

        # printers can either define bDeviceClass=7, or they can define one of
        # their interfaces with bInterfaceClass=7. This class checks for both.
        class FindUsbClass(object):
            def __init__(self, usb_class):

                self._class = usb_class
            def __call__(self, device):
                # first, let's check the device
                if device.bDeviceClass == self._class:
                    return True
                # transverse all devices and look through their interfaces to
                # find a matching class
                for cfg in device:
                    intf = usb.util.find_descriptor(cfg, bInterfaceClass=self._class)

                    if intf is not None:
                        return True

                return False
        #printers = usb.core.find(find_all=True, custom_match=FindUsbClass(0))
        printers = []

        # 067b:2303 Prolific Technology, Inc. PL2303 Serial Port
        printers += usb.core.find(find_all=True, idVendor=0x067b, idProduct=0x2303)

        #0557:2008 ATEN International Co., Ltd UC-232A Serial Port [pl2303]
        printers += usb.core.find(find_all=True, idVendor=0x0557, idProduct=0x2008)

        for printer in printers:
            connected.append({
                'vendor': printer.idVendor,
                'product': printer.idProduct,
                'name': "Serial Port - Datecs",
            })
        return connected

    def lockedstart(self):
        with self.lock:
            if not self.isAlive():
                _logger.info("Status %s:%s:%s" % (self.lock, self.isAlive(), self.daemon))
                self.start()
                #self.daemon = True

    def get_datecs_printer(self, driver):
        if driver == 'Usb':
            driver_name = 'fusb'
            printers = self.connected_usb_devices()
            if len(printers) > 0:
                self.set_status('connected','Connected to '+printers[0]['name'])
                return Usb(printers[0]['vendor'], printers[0]['product'])
            else:
                self.set_status('disconnected','Printer Not Found')
                return None
        elif driver == 'FPrint':
            #driver_name = 'fprint'
            if not self.holdDevice:
                self.holdDevice = FPrint(self.sequence)
            driver = self.holdDevice
            self.set_status('connected','My filename is: '+ driver.get_filename())
            if self.sequence != driver.get_sequence:
                self.sequence = driver.get_sequence
            _logger.info("Datecs fprint %s" % driver)
            return driver

    def get_status(self):
        self.push_task('status')
        return self.status

    def open_cashbox(self,printer):
        printer.cashdraw(2)
        printer.cashdraw(5)

    def set_status(self, status, message = None):
        _logger.info(status+' : '+ (message or 'no message'))
        if status == self.status['status']:
            if message != None and (len(self.status['messages']) == 0 or message != self.status['messages'][-1]):
                self.status['messages'].append(message)
        else:
            self.status['status'] = status
            if message:
                self.status['messages'] = [message]
                self.status['receipt'] = 'print_receipt'
            else:
                self.status['messages'] = []

        if status == 'error' and message:
            _logger.error('Datecs Error: '+message)
        elif status == 'disconnected' and message:
            _logger.warning('Datecs Device Disconnected: '+message)

    def run(self):
        printer = None
        if not datecs:
            _logger.error('Datecs cannot initialize, please verify system dependencies.')
            return
        while True:
            _logger.info("Run task start")
            try:
                error = True
                #_logger.info("Run task start (%s:%s:%s)" % self.queue.get(False))
                timestamp, task, data = self.queue.get(True)

                _logger.info('Datecs task - timestamp, task, data (%s:%s:%s)' % (timestamp, task, data))
                printer = self.get_datecs_printer("FPrint")
                _logger.info('Datecs printer %s' % printer)

                if printer == None:
                    if task != 'status':
                        self.queue.put((timestamp,task,data))
                    error = False
                    time.sleep(5)
                    continue
                elif task == 'receipt': 
                    if timestamp >= time.time() - 1 * 60 * 60:
                        printer.open()
                        self.print_receipt_body(printer,data['receipt'])
                        printer.cut()
                        printer.close()
                elif task == 'xml_receipt':
                    if timestamp >= time.time() - 1 * 60 * 60:
                        printer.open()
                        printer.receipt(data)
                        printer.close()
                elif task == 'cashbox':
                    if timestamp >= time.time() - 12:
                        self.open_cashbox(printer)
                elif task == 'printstatus':
                    self.print_status(printer)
                elif task == 'status':
                    _logger.info('status')
                    pass
                error = False

            except NoDeviceError as e:
                print "No device found %s" %str(e)
            except HandleDeviceError as e:
                print "Impossible to handle the device due to previous error %s" % str(e)
            except TicketNotPrinted as e:
                print "The ticket does not seems to have been fully printed %s" % str(e)
            except NoStatusError as e:
                print "Impossible to get the status of the printer %s" % str(e)
            except Exception as e:
                self.set_status('error', str(e))
                errmsg = str(e) + '\n' + '-'*60+'\n' + traceback.format_exc() + '-'*60 + '\n'
                _logger.error(errmsg)
            finally:
                if error:
                    self.queue.put((timestamp, task, data))
            _logger.info("Run task end %s" % error)

    def push_task(self,task, data = None):
        self.lockedstart()
        _logger.info("Push task %s=>%s" % (task, data))
        self.queue.put((time.time(),task,data))
        _logger.info("Query %s" % self.queue)

    def print_status(self,eprint):
        pass

    def print_receipt_body(self,datecs,receipt):

        def check(string):
            return string != True and bool(string) and string.strip()

        def price(amount):
            return ("{0:."+str(receipt['precision']['price'])+"f}").format(amount)

        def money(amount):
            return ("{0:."+str(receipt['precision']['money'])+"f}").format(amount)

        def quantity(amount):
            if math.floor(amount) != amount:
                return ("{0:."+str(receipt['precision']['quantity'])+"f}").format(amount)
            else:
                return str(amount)

        def printline(left, right='', width=40, ratio=0.5, indent=0):
            lwidth = int(width * ratio)
            rwidth = width - lwidth 
            lwidth = lwidth - indent

            left = left[:lwidth]
            if len(left) != lwidth:
                left = left + ' ' * (lwidth - len(left))

            right = right[-rwidth:]
            if len(right) != rwidth:
                right = ' ' * (rwidth - len(right)) + right

            return ' ' * indent + left + right

        def print_taxes():
            taxes = receipt['tax_details']
            for tax in taxes:
                datecs.text(printline(tax['tax']['name'], price(tax['amount']), width=40,ratio=0.6))

        payment_ticket = receipt.get('advans') and receipt['advans'] != 0 or False
        # Receipt Header
        datecs.new(receipt['cashier_id'],receipt['cashier_password'],False)

        # Orderlines
        for line in receipt['orderlines']:
            pricestr = price(line['price_display'])
            comment = [_('for')+' '+line['unit_name']]
            if (line['product_type'] == 'product' or line['product_type'] == 'money') and not payment_ticket:
                group_stock = line.get('group') and line.get('group') or '1'
                group_vat = line.get('vatgroup') and line['vatgroup'] or '1'
                datecs.sell(line['product_name'],line['price_with_tax'],line['quantity'],group_stock,group_vat)
            elif line['product_type'] == 'money' and payment_ticket:
                group_stock = line.get('group') and line.get('group') or '9'
                group_vat = line.get('vatgroup') and line['vatgroup'] or '1'
                datecs.sell(line['product_name'],line['price_with_tax'],line['quantity'],group_stock,group_vat)
            else:
                datecs.text(printline(line['product_name'], width=48,ratio=0.6))
                comment = [("%s*%s" % (line['quantity'], line['price_with_tax']))+' '+_('for')+' '+line['unit_name']]
            if line['discount'] != 0:
                comment += [_('discount')+' '+line['discount']]
            datecs.text(comment)

        # Footer
        if check(receipt['footer']):
            datecs.text(receipt['footer'])
        datecs.barcode(receipt['ean_uid'])

        # Paymentlines
        for line in receipt['paymentlines']:
            #datecs.text(printline(line['journal'], money(line['amount']), ratio=0.6))
            pay_type = line.get('type') and line['type'] or '0'
            datecs.pay(line['amount'],pay_type)
        if not float_is_zero(receipt['total_with_tax'] - receipt['total_paid'], precision_digits=2):
            datecs.pay(False)


driver = DatecsDriver()

driver.push_task('printstatus')

hw_proxy.drivers['fprint'] = driver

class datecsProxy(hw_proxy.Proxy):

    @http.route('/hw_proxy/print_receipt', type='json', auth='none', cors='*')
    def print_receipt(self, receipt, printer='fprint',funct='validate_order'):
        _logger.info('Datecs: PRINT RECEIPT')
        if hw_proxy.drivers.get(printer):
            hw_proxy.drivers[printer].push_task('receipt',{'receipt': receipt, 'function': funct})

    @http.route('/hw_proxy/print_xml_receipt', type='json', auth='none', cors='*')
    def print_xml_receipt(self, receipt, printer='fprint',funct='validate_order'):
        _logger.info('Datecs: PRINT XML RECEIPT')
        if hw_proxy.drivers.get(printer):
            hw_proxy.drivers[printer].push_task('xml_receipt',{'receipt': receipt, 'function': funct})
