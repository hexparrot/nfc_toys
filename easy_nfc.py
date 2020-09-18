#!/usr/bin/env python3
__author__ = "William Dizon"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "William Dizon"
__email__ = "wdchromium@gmail.com"
__status__ = "Development"

import nfc

TAG_SPECS = {  #defcc size page
    'NTAG213': (0x12, 128, 32),
    'NTAG215': (0x3f, 496, 136),
    'NTAG216': (0x6d, 872, 231),
    'Ultralight': (0x06, 64, 16),
}

class nfc_parser(object):
    def __init__(self, read=True,
                       interface='usb',
                       target_type='106A'):

        self.raw = bytearray()
        self.pages = []

        if read:
            self.clf = nfc.ContactlessFrontend(interface)
            self.target = self.clf.sense(nfc.clf.RemoteTarget(target_type))
            self.tag = nfc.tag.activate(self.clf, self.target)
            self.read()

    def __str__(self):
        retval = []
        try:
            retval.append('Type:      ' + self.tag.type)
            retval.append('Product:   ' + self.tag.product)
            retval.append('UID:       ' + self.uid)
            retval.append('Signature: ' + str(self.signature))
        except AttributeError:
            return '\n'.join(['Type:','Product:','UID:','Signature:'])

        if len(self.pages) >= 3:
            retval.append('Static Lock:  ' + str(self.static_lockpages))
            retval.append('Dynamic Lock: ' + str(self.dynamic_lockpages))

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
    def static_lockpages(self):
        try:
            return self.spaced_hex(self.pages[2][4:])
        except IndexError:
            return None

    @property
    def dynamic_lockpages(self):
        try:
            return self.spaced_hex(self.pages[129][0:6])
        except IndexError:
            return None

    @property
    def tag_type(self):
        if 'NTAG21' in self.tag.product:
            return 'NTAG21{}'.format(self.tag.product[-1])
        else:
            for k,v in TAG_SPECS.items():
                if self.get_page('03h')[2] == v[0]:
                    return k

    @property
    def _pprint(self):
        return ['{}  {}'.format(str(p).zfill(3), self.spaced_hex(d)) for p,d in enumerate(self.pages)]

    def pprint(self):
        print('\n'.join(self._pprint))

    def read(self):
        from itertools import count

        self.raw = bytearray()
        
        try:
            for i in count(0,4):
                d = bytearray(self.tag.read(i)) # tag.read() returns 16 bytes
                [self.raw.append(j) for j in d]

                self.pages.append(d.hex()[0:8])
                self.pages.append(d.hex()[8:16])
                self.pages.append(d.hex()[16:24])
                self.pages.append(d.hex()[24:32])
        except nfc.tag.tt2.Type2TagCommandError:
            num_pages = TAG_SPECS[self.tag_type][2]

            if len(self.pages) > num_pages:
                self.pages = self.pages[0:num_pages]
            if len(self.raw) > num_pages * 4:
                self.raw = bytearray(self.raw[0:num_pages * 4])

    def get_page(self, page_addr):
        if isinstance(page_addr, str) and page_addr[-1] == 'h':
            page_addr = page_addr.rstrip('h')

        retval = bytearray()

        for i in range(4):
            seek = (int(page_addr) * 4) + i
            retval.append(self.raw[seek])

        return retval

    def dump(self):
        with open('dump.bin', 'wb') as fh:
            fh.write(self.raw)

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
