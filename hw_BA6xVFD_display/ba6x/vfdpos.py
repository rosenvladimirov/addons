#!/usr/bin/python
# -*- coding: utf8 -*-

# VFD PoS library for WN USB using PyUSB
# Copyright (C) 2015  Antoine FERRON

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


import usb.core
import usb.util

CODE_PAGE = [{'country_code': 0x30, 'code_page': 'cp437', 'character_set': 'Standard', 'country': 'Latin-America'},
             {'country_code': 0x31, 'code_page': 'cp850', 'character_set': 'Latin 1', 'country': 'International, Scandinavia, Latin-America'},
             {'country_code': 0x32, 'code_page': 'cp852', 'character_set': 'Latin 2', 'country': 'Hungary, Poland, Czechia, Slowakia'},
             {'country_code': 0x33, 'code_page': 'cp857', 'character_set': 'Latin 5/Turkey', 'country': 'Turkey'},
             {'country_code': 0x34, 'code_page': 'cp858', 'character_set': 'Latin 1+€ char', 'country': 'International,Scandinavia,Latin-America'},
             {'country_code': 0x35, 'code_page': 'cp866', 'character_set': 'Latin/Cyrillic', 'country': 'Russia'},
             {'country_code': 0x29, 'code_page': 'cp866', 'character_set': 'Latin/Cyrillic', 'country': 'Russia'},
             {'country_code': 0x37, 'code_page': 'cp862', 'character_set': 'Latin/Hebrew', 'country': 'Israel'},
             {'country_code': 0x36, 'code_page': 'cp737', 'character_set': 'Latin/Greek 2', 'country': 'Greece'},
             {'country_code': 0x38, 'code_page': 'cp874', 'character_set': 'Latin/Greek 2', 'country': 'Greece'},
             {'country_code': 0x63, 'code_page': 'kata', 'character_set': 'Katakana', 'country': 'Japan'},
             {'country_code': 0x73, 'code_page': 'cp437', 'character_set': 'definable', 'country': 'universal'}]
TXT_ENC_KATAKANA_MAP = {
    # Maps UTF-8 Katakana symbols to KATAKANA Page Codes
    # TODO: has this really to be hardcoded?

    # Half-Width Katakanas
    '｡': b'\xa1',
    '｢': b'\xa2',
    '｣': b'\xa3',
    '､': b'\xa4',
    '･': b'\xa5',
    'ｦ': b'\xa6',
    'ｧ': b'\xa7',
    'ｨ': b'\xa8',
    'ｩ': b'\xa9',
    'ｪ': b'\xaa',
    'ｫ': b'\xab',
    'ｬ': b'\xac',
    'ｭ': b'\xad',
    'ｮ': b'\xae',
    'ｯ': b'\xaf',
    'ｰ': b'\xb0',
    'ｱ': b'\xb1',
    'ｲ': b'\xb2',
    'ｳ': b'\xb3',
    'ｴ': b'\xb4',
    'ｵ': b'\xb5',
    'ｶ': b'\xb6',
    'ｷ': b'\xb7',
    'ｸ': b'\xb8',
    'ｹ': b'\xb9',
    'ｺ': b'\xba',
    'ｻ': b'\xbb',
    'ｼ': b'\xbc',
    'ｽ': b'\xbd',
    'ｾ': b'\xbe',
    'ｿ': b'\xbf',
    'ﾀ': b'\xc0',
    'ﾁ': b'\xc1',
    'ﾂ': b'\xc2',
    'ﾃ': b'\xc3',
    'ﾄ': b'\xc4',
    'ﾅ': b'\xc5',
    'ﾆ': b'\xc6',
    'ﾇ': b'\xc7',
    'ﾈ': b'\xc8',
    'ﾉ': b'\xc9',
    'ﾊ': b'\xca',
    'ﾋ': b'\xcb',
    'ﾌ': b'\xcc',
    'ﾍ': b'\xcd',
    'ﾎ': b'\xce',
    'ﾏ': b'\xcf',
    'ﾐ': b'\xd0',
    'ﾑ': b'\xd1',
    'ﾒ': b'\xd2',
    'ﾓ': b'\xd3',
    'ﾔ': b'\xd4',
    'ﾕ': b'\xd5',
    'ﾖ': b'\xd6',
    'ﾗ': b'\xd7',
    'ﾘ': b'\xd8',
    'ﾙ': b'\xd9',
    'ﾚ': b'\xda',
    'ﾛ': b'\xdb',
    'ﾜ': b'\xdc',
    'ﾝ': b'\xdd',
    'ﾞ': b'\xde',
    'ﾟ': b'\xdf',
}

class vfd_pos:
    def __init__(self,pid):
        self.dev = None
        self.codepage = 'cp437'
        self.pid = pid
        self.laststate = False
        self.open()

    def open(self):
        self.dev = usb.core.find(idVendor=0x0aa7, idProduct=self.pid)
        if self.dev is None:
            raise IOError("Error : Connect PoS VFD WN USB")
        try:
            self.dev.detach_kernel_driver(1)
        except:
            pass
        try:
            cfg=self.dev[0]
            ep = cfg[(0,0)][1]
            assert ep is not None
            if ep.wMaxPacketSize!=32:
                ep = cfg[(1,0)][1]
            print ep
            assert ep.wMaxPacketSize==32
            self.endpoint = ep
            self.laststate = True
            return True
        except:
            raise IOError("Error initializing VFD")
            self.set_charset(0x30)
            self.clearscreen()
            self.poscur(0,0)
            self.laststate = False
            return False

    def close(self):
        i = 0
        while True:
            try:
                if not self.dev.is_kernel_driver_active(1):
                    usb.util.release_interface(self.dev, 1)
                    self.dev.attach_kernel_driver(1)
                    usb.util.dispose_resources(self.dev)
                else:
                    self.dev = None
                    self.laststate = False
                    return True
            except usb.core.USBError as e:
                i += 1
                if i > 10:
                    self.laststate = False
                    return False
            sleep(0.1)

    def status(self):
        if self.dev is None:
            return self.open()
        return self.laststate

    def clear(self):
        self.clearscreen()

    def send_buffer(self,buffer):
        self.endpoint.write(buffer)

    def selftest(self):
        buffer = [0x00]*32
        buffer[1] = 0x10
        self.send_buffer(buffer)

    def reset(self):
        buffer = [0x00]*32
        buffer[1] = 0x40
        self.send_buffer(buffer)

    def send_ctrl_seq(self,esc_seq):
        buffer = [0x00]*32
        buffer[0] = 0x02
        len_seq = len(esc_seq)
        buffer[2] = len_seq
        for datx in range(0, len_seq):
            buffer[3+datx] = esc_seq[datx]
        self.send_buffer(buffer)

    def set_charset(self,chrset):
        self.send_ctrl_seq( [0x1B, 0x52, chrset] )
        for codepage in CODE_PAGE:
            print codepage['country_code']
            if codepage['country_code'] == chrset:
                self.codepage = codepage['code_page']
                break

    def set_str_charset(self,charset):
        for codepage in CODE_PAGE:
            print codepage['code_page']
            if codepage['code_page'] == chrset:
                self.codepage = codepage['code_page']
                self.send_ctrl_seq( [0x1B, 0x52, codepage['country_code']] )
                break


    def clearscreen(self):
        self.send_ctrl_seq( [0x1B, 0x5B, 0x32, 0x4A] )

    def printchr(self,chr):
        self.send_ctrl_seq( [chr] )

    def poscur(self,line,col):
        seq=[]
        seq.append( 0x1B )
        seq.append( 0x5B )
        assert( 0 <= line <= 9)
        seq.append( 0x30 + line )
        seq.append( 0x3B )
        assert( 0 <= col <= 99)
        diz,unit = divmod(col,10)
        seq.append( 0x30 + diz)
        seq.append( 0x30 + unit)
        seq.append( 0x48 )
        self.send_ctrl_seq( seq )

    def encode_katakana(text):
        """I don't think this quite works yet."""
        encoded = []
        for char in text:
            if jaconv:
                # try to convert japanese text to half-katakanas
                char = jaconv.z2h(jaconv.hira2kata(char))
                # TODO: "the conversion may result in multiple characters"
                # If that really can happen (I am not really shure), than the string would have to be split and every single
                #  character has to passed through the following lines.

            if char in TXT_ENC_KATAKANA_MAP:
                encoded.append(TXT_ENC_KATAKANA_MAP[char])
            else:
                # TODO doesn't this discard all that is not in the map? Can we be sure that the input does contain only
                # encodable characters? We could at least throw an exception if encoding is not possible.
                pass
        return b"".join(encoded)

    def write_msg(self,msgu):
        if self.codepage == 'kata':
            msg = self.encode_katakana(msgu)
        else:
            msg = msgu.encode(self.codepage, 'replace')

        while msg:
            msg_chr = list(msg)[0:29]
            self.send_ctrl_seq(map( ord, msg_chr ))
            msg = msg[29:]
