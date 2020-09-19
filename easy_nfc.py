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
    def __init__(self, interface='usb', target_type='106A'):
        """
        A high-level interface to quickly read an NFC tag.
        Heavily integrates 'nfc' module for functionality and hardware support.
        This class is designed to assist in bulk-read and write operations.

        Parameters:
        interface (str): Defaults to 'usb'; other interfaces are available
                         but usb is most frequently-used value.
        target_type (str): Sense cards at 106kbps, type A target by default.
                           Available: '106A', '106B', '212F'

        Returns: Nothing

        """

        self.clf = nfc.ContactlessFrontend(interface)
        self.target = self.clf.sense(nfc.clf.RemoteTarget(target_type))
        self.tag = nfc.tag.activate(self.clf, self.target)
        self.raw = nfc.tag.tt2.Type2TagMemoryReader(self.tag)

    def __str__(self):
        """
        Returns a string-representation of the nfc_parser object
        Provides a big-picture view of the detected tag, along with
        any information on locks and the first four pages of data
        """

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
        """ Returns the tag identifier from nfc module in hex format """
        return self.tag.identifier.hex()

    @property
    def signature(self):
        """
        Returns the tag signature if one exists.
        Tag signatures are known to exist in any NTAG21* devices
        """
        try:
            return self.tag.signature.hex()
        except AttributeError:
            return None

    @property
    def pages(self):
        """
        Returns all the pages of the nfc tag as a list of hexadecimal
        strings with no space padding.
        """

        num_pages = TAG_SPECS[self.tag_type].pages
        return [self.get_page(i).hex() for i in range(0, num_pages)]

    @property
    def static_lockpages(self):
        """
        Returns Page 002h, Byte 2,3 of an nfc tag.  This is likely present
        on all cards that are not uid-only cards (nodata)
        """

        try:
            return self.spaced_hex(self.get_page(2)[2:])
        except TypeError:
            return None

    @property
    def dynamic_lockpages(self):
        """
        Returns Page 130h, Byte 1,2,3 of an nfc tag.
        This is only present on NTAG215 cards.
        """
        try:
            return self.spaced_hex(self.get_page(130)[0:3])
        except TypeError:
            return None

    @property
    def tag_type(self):
        """
        Attempts to identify the tag type based on the product name.

        While similarly-named properties exist such as tag.type,
        this is often insufficent for determining the capabilities
        and capacities, e.g., "Type2Tag" does not convey pagecounts.

        In fact, if no known product is identified, tag.type is returned
        which appears to be the default state of UID-only cards.
        """

        if 'NTAG21'.lower() in self.tag.product.lower():
            return 'NTAG21{}'.format(self.tag.product[-1])
        elif 'ultralight' in self.tag.product.lower():
            return 'Ultralight'
        else:
            return self.tag.type

    @property
    def uid_only(self):
        """
        If tag.type matches the tag.product properties, the card is an
        UID-only nfc device.
        """

        try:
            return self.tag.type == self.tag.product
        except AttributeError:
            return None

    @property
    def oem_bytes(self):
        """ Checks if current nfc tag has factory default values set. """
        try:
            for loc, d_bytes in OEM_BYTES.get(self.tag_type):
                assert(self.get_page(loc) == d_bytes)
        except AssertionError:
            return False
        else:
            return True

    @property
    def _pprint(self):
        """
        Generates the list used by the pprint method to show
        enumerated, spaced hex format of all nfc tag's pages.
        """
        return ['{}  {}'.format(str(p).zfill(3), self.spaced_hex(d)) for p,d in enumerate(self.pages)]

    def pprint(self):
        """ Prints to stdout a tabularized hexadecimal output of the nfc tag contents """
        print('\n'.join(self._pprint))

    def get_page(self, page_addr):
        """
        Retreive the contents of a page from the active card's memory.

        Parameters:
        page_addr (str, int): hexadecimal or decimal value accepted

        Returns: bytes() object of len(4) containing the requested page.

        """

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

    def write_page(self, page_addr, instr):
        """
        Alias function for tag.write.

        Parameters:
        page_addr (int): decimal value for page
        instr (bytes/bytearray): 4 bytes to be written to card

        Returns: None
        """
        self.tag.write(page_addr, instr)

    def dump(self):
        """ Dumps current tag to 'dump.bin' file in script directory """
        with open('dump.bin', 'wb') as fh:
            fh.write(self.raw[0:TAG_SPECS[self.tag_type].pages * 4])

    def commit_image(self):
        """
        Writes 'dump.bin' to current card.
        TODO: make checks to see if locks are written or confirmations required.
        """
        with open('dump.bin', 'rb') as fh:
            page = 0
            while page < TAG_SPECS[self.tag_type].pages:
                next_four = fh.read(4)
                if page not in [0,1,2,130]:
                    self.tag.write(page, next_four)
                page += 1

    @staticmethod
    def spaced_hex(instr):
        """ Receives a str of hexes or bytes and spaces it out -> AA BB CC DD """
        if isinstance(instr, bytes):
            instr = instr.hex()
        if len(instr) % 2:
            raise RuntimeError('Provided string must be even-numbered in length')
        return ' '.join(instr[i:i+2] for i in range(0, len(instr), 2))

if __name__ == '__main__':
    ni = nfc_parser()
    print(ni)
