# -*- coding: utf-8 -*-

import logging
import os
import csv
import tempfile
import time
import copy
import io
import base64
import math
import md5
import re
import traceback
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

from PIL import Image

try:
    import jcconv
except ImportError:
    jcconv = None

try: 
    import qrcode
except ImportError:
    qrcode = None

from exceptions import *

try: 
    import html2text
except:
    from openerp.addons.email_template import html2text

_logger = logging.getLogger(__name__)

class Datecs:
    """ Datecs Printer object """
    device    = None
    encoding  = None
    mode      = 'fprint'
    img_cache = {}
    filename  = os.path.join("fprint", "for_print", "") + "in.inp"
    lines     = []
    sequence  = 0
    dictcmd   = {
                "text": "P,%s,______,_,__;%.30s;%.30s;%.30s;%.30s;%.30s;",
                "sell":  "S,%s,______,_,__;%.20s;%9.2f;%9.3f;%s;%s;%s;",
                "dep_sell": "E,%s,______,_,__;%.20s;%9.2f;%9.3f;%s;%s;%s;0;0;",
                "pay": "T,%s,______,_,__;%s;%9.2f;",
                "payall": "T,%s,______,_,__;",
                "disc_marg": "C,%s,______,_,__;1;%s;;;;",
                "add_marg": "C,%s,______,_,__;0;%s;;;;",
                "give_money": "I,%s,______,_,__;0;%s;;;;",
                "take_money": "I,%s,______,_,__;1;%s;;;;",
                "service_receipt": "Y,%s,______,_,__;%s;%s;%s;%s;%s;",
                "z_report": "Z,%s,______,_,__;",
                "dublicate": "D,%s,______,_,__;",
                "beep": "B,%s,______,_,__;",
                "open": "48,%s,______,_,__;%s;%s;%s;%s",
                "barcode": "A,%s,______,_,__;%s;%s;",
                }

    def receipt(self,xml):
        """
        Prints an xml based receipt definition
        """
#        try:
        #root            = ET.fromstring(xml.encode('utf-8'))
        #print xml
        text = html2text.html2text(xml) #.decode('utf8','replace'))  
        text = text.replace(chr(13), '\n')
        text = text.replace('\n\n', '\r\n')
        self._raw(text)

    def _raw(self, txt):
        self.lines.append(txt)

    def get_sequence():
        return self.sequence

    def set_sequence(self,sq):
        self.sequence = sq
        if self.sequence < 99:
            self.sequence = self.sequence + 1
        else:
            self.sequence = 0

    def new(self,user,password,depart,invoice=False):
        content = self.dictcmd['open'] % (self.sequence, user, password, depart or 1, invoice and 1 or 0)
        self._raw(content)

    def barcode(self,value):
        content = self.dictcmd['barcode'] % (self.sequence,"2",value)
        self._raw(content)

    def text(self,txt):
        if not txt:
            return
        if isinstance(txt, (str, unicode)):
            txt = [txt]
        """ Print Utf8 encoded alpha-numeric text """
        for i, element in enumerate(txt):
            try:
                txt[i] = element.decode('utf-8')
            except:
                try:
                    txt[i] = element.decode('utf-16')
                except:
                    pass

        (txt1, txt2, txt3, txt4, txt5) = tuple(txt + [""]*(5-len(txt)))
        content = self.dictcmd['text'] % (self.sequence, txt1, txt2, txt3, txt4, txt5)
        self._raw(content)

    def sell(self, name, price, qty, group, vat):
        content = self.dictcmd['sell'] % (self.sequence, name, price, qty, "1", group, vat)
        self._raw(content)

    def pay(self, amount, type = "cash"):
        if not amount:
            content = self.dictcmd['payall'] % (self.sequence)
        else:
            if type == "cash":
                type = "0"
            content = self.dictcmd['pay'] % (self.sequence,type,amount)
        self._raw(content)

    def set(self, align='left', font='a', type='normal', width=1, height=1):
        """ Set text properties """
        pass

    def cut(self, mode=''):
        """ Cut paper """
        pass

    def cashdraw(self, pin):
        """ Send pulse to kick the cash drawer """
        pass

    def hw(self, hw):
        """ Hardware operations """
        pass

    def control(self, ctl):
        """ Feed control sequences """
        pass
