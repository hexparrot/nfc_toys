#!/usr/bin/env python3
__author__ = "William Dizon"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "William Dizon"
__email__ = "wdchromium@gmail.com"
__status__ = "Development"

import nfc
from collections import namedtuple

Tag_Def = namedtuple('tag_definition', 'cc size pages')
TAG_SPECS = {
    'NTAG213': Tag_Def(0x12, 128, 32),
    'NTAG215': Tag_Def(0x3e, 496, 135),
    'NTAG216': Tag_Def(0x6d, 872, 231),
    'Ultralight': Tag_Def(0x06, 64, 16),
    'Type2Tag': Tag_Def(0x00, 0, 0),
}

OEM_BYTES = { # https://www.nxp.com/docs/en/data-sheet/NTAG213_215_216.pdf
    'NTAG213': [('03h', bytes([0xe1, 0x10, 0x12, 0x00])),
                ('04h', bytes([0x01, 0x03, 0xa0, 0x0c])),
                ('05h', bytes([0x34, 0x03, 0x00, 0xfe]))],
    'NTAG215': [('03h', bytes([0xe1, 0x10, 0x3e, 0x00])),
                ('04h', bytes([0x03, 0x00, 0xfe, 0x00])),
                ('05h', bytes([0x00, 0x00, 0x00, 0x00]))],
    'NTAG216': [('03h', bytes([0xe1, 0x10, 0x6d, 0x00])),
                ('04h', bytes([0x03, 0x00, 0xfe, 0x00])),
                ('05h', bytes([0x00, 0x00, 0x00, 0x00]))],
}

class nfc_parser(object):
    def __init__(self, read=True,
                       interface='usb',
                       target_type='106A'):

        if read:
            self.clf = nfc.ContactlessFrontend(interface)
            self.target = self.clf.sense(nfc.clf.RemoteTarget(target_type))
            self.tag = nfc.tag.activate(self.clf, self.target)
            self.raw = nfc.tag.tt2.Type2TagMemoryReader(self.tag)
        else:
            self.raw = bytearray()

    def __str__(self):
        retval = []
        try:
            retval.append('Type        : ' + self.tag.type)
            retval.append('Product     : ' + self.tag.product)
            retval.append('UID         : ' + self.uid)
            retval.append('Signature   : ' + str(self.signature))
            retval.append('Static Lock : ' + str(self.static_lockpages))
            retval.append('Dynamic Lock: ' + str(self.dynamic_lockpages))
        except AttributeError:
            return '\n'.join([p.ljust(12, ' ') + ':' for p in 
                ['Type','Product','UID','Signature', 'Static Lock', 'Dynamic Lock']])

        retval.append('')
        retval.extend(self.tag.dump()[0:4])
        return '\n'.join(retval)

    @property
    def uid(self):
        return self.tag.identifier.hex()

    @property
    def signature(self):
        try:
            return self.tag.signature.hex()
        except AttributeError:
            return None

    @property
    def pages(self):
        num_pages = TAG_SPECS[self.tag_type].pages
        return [self.get_page(i).hex() for i in range(0, num_pages)]

    @property
    def static_lockpages(self):
        try:
            return self.spaced_hex(self.get_page(2)[2:])
        except TypeError:
            return None

    @property
    def dynamic_lockpages(self):
        try:
            return self.spaced_hex(self.get_page(130)[0:3])
        except TypeError:
            return None

    @property
    def tag_type(self):
        if 'NTAG21'.lower() in self.tag.product.lower():
            return 'NTAG21{}'.format(self.tag.product[-1])
        elif 'ultralight' in self.tag.product.lower():
            return 'Ultralight'
        else:
            return self.tag.type

    @property
    def uid_only(self):
        try:
            return self.tag.type == self.tag.product
        except AttributeError:
            return None

    @property
    def oem_bytes(self):
        try:
            for loc, d_bytes in OEM_BYTES.get(self.tag_type):
                assert(self.get_page(loc) == d_bytes)
        except AssertionError:
            return False
        else:
            return True

    @property
    def _pprint(self):
        return ['{}  {}'.format(str(p).zfill(3), self.spaced_hex(d)) for p,d in enumerate(self.pages)]

    def pprint(self):
        print('\n'.join(self._pprint))

    def get_page(self, page_addr):
        if isinstance(page_addr, str) and page_addr[-1] == 'h':
            page_addr = page_addr.rstrip('h')
        page = int(page_addr)

        if self.uid_only:
            return None
        else:
            try:
                return bytes(self.raw[page * 4:page * 4 + 4])
            except nfc.tag.tt2.Type2TagCommandError:
                return None

    def dump(self):
        with open('dump.bin', 'wb') as fh:
            fh.write(self.raw[0:TAG_SPECS[self.tag_type].pages * 4])

    @staticmethod
    def spaced_hex(instr):
        # Receives a str of hexes or bytes and spaces it out -> AA BB CC DD
        if isinstance(instr, bytes):
            instr = instr.hex()
        if len(instr) % 2:
            raise RuntimeError('Provided string must be even-numbered in length')
        return ' '.join(instr[i:i+2] for i in range(0, len(instr), 2))

if __name__ == '__main__':
    ni = nfc_parser()
    print(ni)
