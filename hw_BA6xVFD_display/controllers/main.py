# -*- encoding: utf-8 -*-
##############################################################################
#
#    Hardware Customer Display module for Odoo
#    Copyright (C) 2014 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import logging
import simplejson
import time
import time as time_
import math
from threading import Thread, Lock
from Queue import Queue
import openerp.addons.hw_proxy.controllers.main as hw_proxy
from openerp import http
from openerp.tools.config import config
from openerp.tools.translate import _

from .. ba6x import *
from .. ba6x.exceptions import *
from .. ba6x.ba6x import Display

_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
except (ImportError, IOError) as err:
    _logger.debug(err)

# workaround https://bugs.launchpad.net/openobject-server/+bug/947231
# related to http://bugs.python.org/issue7980
from datetime import datetime
datetime.strptime('2012-01-01', '%Y-%m-%d')
driver_name = 'ba6xvfd'

class CustomerDisplayDriver(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.setDaemon(True)
        self.queue = Queue()
        self.lock = Lock()
        self.seep5muntes = False;
        self.remaining = 0;

        self.status = {'status': 'connecting', 'messages': []}
        self.device_name = config.get(
            'customer_display_device_name', '0x200')
        self.device_charset = config.get(
            'customer_display_device_charset', '0x35')
        self.holdDevice = Display(0x200)
        self.holdDevice.set_charset(0x35)

    def get_status(self):
        self.push_task('status')
        return self.status

    def set_status(self, status, message=None):
        if status == self.status['status']:
            if message is not None and message != self.status['messages'][-1]:
                self.status['messages'].append(message)
        else:
            self.status['status'] = status
            if message:
                self.status['messages'] = [message]
            else:
                self.status['messages'] = []

        if status == 'error' and message:
            _logger.error('Display Error: '+message)
        elif status == 'disconnected' and message:
            _logger.warning('Disconnected Display: '+message)

    def lockedstart(self):
        with self.lock:
            if not self.isAlive():
                self.start()

    def push_task(self, task, data=None):
        self.lockedstart()
        self.queue.put((time.time(), task, data))

    def run(self):
        while True:
            present_time = time.localtime()
            #_logger.info("Remaining %s" % present_time.tm_sec - self.remaining)
            showOnTime = False

            if self.seep5muntes and (int(round(time_.time() * 1000)) - self.remaining >= 300000 or self.remaining == 0):
                self.remaining = int(round(time_.time() * 1000))
                self.seep5muntes = False
            if not self.seep5muntes and (int(round(time_.time() * 1000)) - self.remaining >= 60000 or self.remaining == 0):
                self.remaining = int(round(time_.time() * 1000))
                showOnTime = True

            try:
                timestamp, task, data = self.queue.get(True)
                if self.holdDevice.status():
                    self.set_status('connected', 'Display is ready')
                if task == 'receipt':
                    self.seep5muntes = True
                    self.remaining = present_time.tm_sec
                    self.print_receipt_body(self.holdDevice,data['receipt'],data['function'])
                elif task == 'status':
                    if showOnTime:
                        self.printdate(present_time)
                    pass
            except Exception as e:
                self.set_status('error', str(e))

    def printdate(self, present_time):
        #_logger.info("Show date %a %d %b %Y %H:%M" % present_time)
        date = time.strftime("%a %d %b %Y", present_time).center(20)
        hour = time.strftime("%H:%M", present_time).center(20)
        date = unicode(date, 'utf-8')
        hour = unicode(hour, 'utf-8')
        _logger.info("Datetime now is: %s::%s" % (date, hour))
        self.holdDevice.clear()
        self.holdDevice.cursor(1,1)
        self.holdDevice._raw(date)
        self.holdDevice.cursor(2,1)
        self.holdDevice._raw(hour)


    def print_receipt_body(self,printer,receipt,function='addProduct'):

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

        def display_text(lines):
            _logger.debug(
                "Preparing to send the following lines to LCD: %s" % lines)
            # We don't check the number of rows/cols here, because it has already
            # been checked in the POS client in the JS code
            row = 0
            printer.clear()
            for dline in lines:
                printer.cursor(row, 0)
                printer._raw(dline)
                row = (row == 0) and 2 or 0
            #row = (row ==  0 and len(dline) <= 30) and 2 or 0
        if function == 'addProduct':
            #_logger.info("Get line %s" % receipt.get('ordercurrentline'))
            if receipt.get('ordercurrentline'):
                data = []
                line = receipt['ordercurrentline']
                data.append(printline(line['product_name'],width=20,ratio=1))
                data.append(printline(quantity(line['quantity'])+'*', price(line['price_with_tax']), width=20,ratio=0.4))
                display_text(data)
        elif function == 'validate_order':
            #_logger.info("Get line %s" % receipt)
            data = []
            data.append(_('Total').center(20))
            data.append(price(receipt['total_with_tax']).center(20))
            display_text(data)

driver = CustomerDisplayDriver()

hw_proxy.drivers[driver_name] = driver

class CustomerDisplayProxy(hw_proxy.Proxy):
    @http.route('/hw_proxy/print_receipt', type='json', auth='none', cors='*')
    def print_receipt(self, receipt, printer='ba6xvfd', funct='addProduct'):
        if hw_proxy.drivers.get(printer) and funct in ['addProduct', 'validate_order']:
            hw_proxy.drivers[printer].push_task('receipt',{'receipt': receipt, 'function': funct})
