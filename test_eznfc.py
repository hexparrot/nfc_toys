#!/usr/bin/env python3
__author__ = "William Dizon"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "William Dizon"
__email__ = "wdchromium@gmail.com"
__status__ = "Development"

import unittest
from easy_nfc import nfc_parser, TAG_SPECS

class TestNFCDump(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_read(self):
        ni = nfc_parser(read=False)
        self.assertEqual(len(ni.raw), 0)
        self.assertEqual(len(ni.pages), 0)

        ni = nfc_parser()

        num_pages = TAG_SPECS[ni.tag_type].pages
        self.assertEqual(len(ni.pages), num_pages)

        uid_start = ni.raw[0:3].hex() + ni.raw[4:8].hex()
        self.assertEqual(uid_start, ni.uid)
        
        self.assertEqual(nfc_parser.spaced_hex(uid_start),
                         nfc_parser.spaced_hex(ni.uid))

    def test_get_uid(self):
        ni = nfc_parser()
        self.assertEqual(len(ni.uid), 14)

    def test_get_signature(self):
        ni = nfc_parser()
        if ni.tag.product.startswith('NXP NTAG'):
            self.assertEqual(len(ni.signature), 64)
        else:
            self.assertIsNone(ni.signature)

    def test_spaced_hex(self):
        self.assertEqual(nfc_parser.spaced_hex(b'\x04\x1f\x06\xd2\\d\x85'),
                         '04 1f 06 d2 5c 64 85')
        self.assertEqual(nfc_parser.spaced_hex('041f06d25c6485'),
                         '04 1f 06 d2 5c 64 85')
        with self.assertRaises(RuntimeError): #incomplete page dump
            nfc_parser.spaced_hex('041f06d')

    def test_str(self):
        ni = nfc_parser(read=False)
        str_rep = str(ni)
        split = str_rep.split('\n')

        self.assertEqual(split[0], 'Type:')
        self.assertEqual(split[1], 'Product:')
        self.assertEqual(split[2], 'UID:')
        self.assertEqual(split[3], 'Signature:')

        with self.assertRaises(IndexError): #stuff isnt read yet
            self.assertEqual(split[4], '')

        ni = nfc_parser()
        str_rep = str(ni)
        split = str_rep.split('\n')
        self.assertEqual(split[0], 'Type:      {0}'.format(ni.tag.type))
        self.assertEqual(split[1], 'Product:   {0}'.format(ni.tag.product))
        self.assertEqual(split[2], 'UID:       {0}'.format(ni.uid))
        if ni.tag.product.startswith('NXP NTAG'):
            self.assertEqual(split[3], 'Signature: {0}'.format(ni.signature))
        else:
            self.assertEqual(split[3], 'Signature: {0}'.format('None'))

        self.assertEqual(split[4], 'Static Lock:  {0}'.format(ni.static_lockpages))
        self.assertEqual(split[5], 'Dynamic Lock: {0}'.format(ni.dynamic_lockpages or str(None)))

        dump = ni.tag.dump()
        self.assertEqual(split[6], '')
        self.assertEqual(split[7], dump[0])
        self.assertEqual(split[8], dump[1])
        self.assertEqual(split[9], dump[2])
        self.assertEqual(split[10], dump[3])

    def test_static_lockpages(self):
        ni = nfc_parser(read=False)
        self.assertEqual(ni.static_lockpages, None)
        ni = nfc_parser()
        self.assertEqual(ni.static_lockpages, '00 00')

    def test_dynamic_lockpages(self):
        ni = nfc_parser(read=False)
        self.assertEqual(ni.dynamic_lockpages, None)
        ni = nfc_parser()

        if ni.tag.product == 'NXP NTAG215':
            self.assertEqual(ni.dynamic_lockpages, '00 00 00')
        elif 'Mifare Ultralight (MF01CU1)':
            self.assertIsNone(ni.dynamic_lockpages)

    def test_dump(self):
        from pathlib import Path
        import os

        ni = nfc_parser()
        ni.dump()

        dumpfile = Path('./dump.bin')
        self.assertTrue(dumpfile.exists())

        num_pages = TAG_SPECS[ni.tag_type].pages
        self.assertEqual(os.stat(dumpfile).st_size, 4 * num_pages)

        with open(dumpfile, 'rb') as df:
            raw = df.read()
        self.assertEqual(bytes(raw), ni.raw[0:TAG_SPECS[ni.tag_type].pages * 4])

    def test_pprint(self):
        ni = nfc_parser(read=False)
        self.assertEqual(len(ni._pprint), 0)

        ni = nfc_parser()
        num_pages = TAG_SPECS[ni.tag_type].pages
        self.assertEqual(len(ni._pprint), num_pages)

        for i in range(num_pages):
            self.assertEqual(ni._pprint[i], '{:>03}  {}'.format(i,ni.spaced_hex(ni.pages[i])))

    def test_get_page(self):
        ni = nfc_parser()

        #for NXP NTAG215
        MANUFACTURE_ID = 0x04

        b = ni.get_page('00h')
        self.assertEqual(b[0], MANUFACTURE_ID)
        self.assertEqual(len(b), 4)

        b = ni.get_page('00')
        self.assertEqual(b[0], MANUFACTURE_ID)
        self.assertEqual(len(b), 4)

        b = ni.get_page(0)
        self.assertEqual(b[0], MANUFACTURE_ID)
        self.assertEqual(len(b), 4)

    def test_tag_type(self):
        ni = nfc_parser()
        if not ni.signature:
            self.assertEqual(ni.tag_type, 'Ultralight')
        else:
            self.assertTrue(ni.tag_type, ['NTAG213', 'NTAG215', 'NTAG216'])

if __name__ == '__main__':
    unittest.main()

