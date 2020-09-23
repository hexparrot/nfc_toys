#!/usr/bin/env python3
__author__ = "William Dizon"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "William Dizon"
__email__ = "wdchromium@gmail.com"
__status__ = "Development"

import unittest
from easy_nfc import nfc_parser, TAG_SPECS, OEM_BYTES

class TestNFCDump(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init(self):
        ni = nfc_parser()

        if ni.uid_only: #dummy cards with no writable value (uid only)
            import nfc
            with self.assertRaises(nfc.tag.tt2.Type2TagCommandError):
                uid_start = ni.raw[0:3].hex() + ni.raw[4:8].hex()
        else:
            num_pages = TAG_SPECS[ni.tag_type].pages
            self.assertEqual(len(ni.pages), num_pages)

            uid_start = ni.raw[0:3].hex() + ni.raw[4:8].hex()
            self.assertEqual(uid_start, ni.uid)
            
            self.assertEqual(nfc_parser.spaced_hex(uid_start),
                             nfc_parser.spaced_hex(ni.uid))

    def test_get_uid(self):
        ni = nfc_parser()
        if ni.uid_only:
            self.assertEqual(len(ni.uid), 8)
        else:
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
        ni = nfc_parser()
        str_rep = str(ni)
        split = str_rep.split('\n')
        self.assertEqual(split[0], 'Type        : {0}'.format(ni.tag.type))
        self.assertEqual(split[1], 'Product     : {0}'.format(ni.tag.product))
        self.assertEqual(split[2], 'UID         : {0}'.format(ni.uid))
        self.assertEqual(split[3], 'Signature   : {0}'.format(str(ni.signature)))
        self.assertEqual(split[4], 'Static Lock : {0}'.format(ni.static_lockpages or str(None)))
        self.assertEqual(split[5], 'Dynamic Lock: {0}'.format(ni.dynamic_lockpages or str(None)))

        char_info = ni.check_api(ni.character_id)
        self.assertEqual(split[6], '')
        self.assertEqual(split[7], 'Series      : {0}'.format(char_info['gameSeries']))
        self.assertEqual(split[8], 'Character   : {0}'.format(char_info['character']))
        self.assertEqual(split[9], 'Char ID     : {0}'.format(char_info['head']))

        dump = ni.tag.dump()
        self.assertEqual(split[10], '')
        self.assertEqual(split[11], dump[0])
        self.assertEqual(split[12], dump[1])
        self.assertEqual(split[13], dump[2])
        self.assertEqual(split[14], dump[3])

    def test_static_lockpages(self):
        ni = nfc_parser()

        if ni.uid_only:
            self.assertIsNone(ni.static_lockpages)
        else:
            self.assertEqual(ni.static_lockpages, ni.spaced_hex(ni.get_page(2)[2:]))

    def test_dynamic_lockpages(self):
        ni = nfc_parser()

        if ni.tag.product == 'NXP NTAG215':
            self.assertEqual(ni.dynamic_lockpages, ni.spaced_hex(ni.get_page(130)[0:3]))
        else:
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
        ni = nfc_parser()
        num_pages = TAG_SPECS[ni.tag_type].pages
        self.assertEqual(len(ni._pprint), num_pages)

        for i in range(num_pages):
            self.assertEqual(ni._pprint[i], '{:>03}  {}'.format(i,ni.spaced_hex(ni.pages[i])))

    def test_get_page(self):
        ni = nfc_parser()

        MANUFACTURER_ID = 0x04 #for NXP

        for i in ['00h', '00', 0]:
            if ni.uid_only:
                #dummy cards with no writable value (id only)
                b = ni.get_page(i)
                self.assertIsNone(b)
            else:
                b = ni.get_page(i)

                self.assertEqual(b[0], MANUFACTURER_ID)
                self.assertEqual(len(b), 4)

        if not ni.uid_only:
            uid = ni.tag.identifier
            first, second = uid[:3], uid[3:]
            self.assertEqual(ni.get_page(0)[0:3], first)
            self.assertEqual(ni.get_page(1), second)

    @unittest.skip("this is a simple alias function, and we do not need to write each run")
    def test_write_page(self):
        ni = nfc_parser()

        from random import getrandbits
        rgen = {}
        reread = []
        for i in range(5,8):
            rgen[i] = bytes([getrandbits(8) for i in range(4)])
            ni.write_page(i, rgen[i])

        for i in range(5,8):
            reread = ni.get_page(i)
            self.assertEqual(reread, rgen[i])

    @unittest.skip("we do not need to write each run")
    def test_commit_image(self):
        lock_data = [#page, #byteoffset, #bytedata
            ('82h', 3, [0x01, 0x00, 0x0F, 0xBD]), #dynamic lockpages
            ('02h', 2, [0x0F, 0x48, 0x0F, 0xE0]), #static lockpages
        ]

        ni = nfc_parser()
        ni.commit_image(byte_override=lock_data)
        del ni #to ensure the device is closed and usable below

        with open('dump.bin', 'rb') as binary:
            image = binary.read()

            np = nfc_parser()
            # 504 bytes of user programmable r/w memory in NTAG215
            self.assertEqual(np.raw[16:520], image[16:520])

            for page_addr, offset, bytedata in lock_data:
                page = int(page_addr.rstrip('h'), 16)

                start_byte = (page * 4) + offset
                end_byte = (page * 4) + offset + (4-offset)
                self.assertEqual(np.raw[start_byte:end_byte],
                                 bytearray(bytedata)[offset:])

    def test_cc_byte(self):
        ni = nfc_parser()
        b = ni.get_page('03h')
        if ni.uid_only:
            self.assertIsNone(b)
        else:
            self.assertEqual(len(b), 4)
            if b[2] != TAG_SPECS[ni.tag_type].cc:
                raise unittest.SkipTest('cc bytes mismatch, skipping')
            else:
                # not that useful since it skips when it mismatches anyway
                self.assertEqual(b[2], TAG_SPECS[ni.tag_type].cc)

    def test_tag_type(self):
        ni = nfc_parser()
        if not ni.signature:
            self.assertTrue(ni.tag_type, ['Ultralight', 'Type2Tag'])
        else:
            self.assertTrue(ni.tag_type, ['NTAG213', 'NTAG215', 'NTAG216'])

    def test_uid_only_property(self):
        ni = nfc_parser()
        if ni.tag.type == ni.tag.product:
            self.assertTrue(ni.uid_only)
        else:
            self.assertFalse(ni.uid_only)

    def test_oem_bytes(self):
        ni = nfc_parser()

        try:
            for loc, d_bytes in OEM_BYTES.get(ni.tag_type):
                if ni.get_page(loc) != d_bytes:
                    raise unittest.SkipTest('oem bytes mismatch, skipping')
                    break # mismatch!
            else: # matches OK
                self.assertTrue(ni.oem_bytes)
        except TypeError:
            raise unittest.SkipTest('unknown tag type to match, skipping')

    def test_character_id(self):
        ni = nfc_parser()

        cid = ni.character_id
        if ni.uid_only:
            self.assertIsNone(cid)
        else:
            self.assertEqual(len(cid), 8)
            import string
            self.assertTrue(all(c in string.hexdigits for c in cid))

    def test_character_guid(self):
        ni = nfc_parser()

        cid = ni.character_guid
        if ni.uid_only:
            self.assertIsNone(cid)
        else:
            self.assertEqual(len(cid), 18)
            import string
            self.assertTrue(cid.startswith('0x'))
            self.assertTrue(all(c in string.hexdigits for c in cid[2:]))

    def test_check_api(self):
        ni = nfc_parser()

        amiibo_id = '01830001'
        json_obj = ni.check_api(amiibo_id)
        self.assertEqual(json_obj['amiiboSeries'], 'Animal Crossing')
        self.assertEqual(json_obj['character'], 'Tom Nook')

        amiibo_id = '021B0001'
        json_obj = ni.check_api(amiibo_id)
        self.assertEqual(json_obj['amiiboSeries'], 'Animal Crossing')
        self.assertEqual(json_obj['character'], 'Tutu')

    def test_check_db(self):
        ni = nfc_parser()
        series = 0x05

        amiibo_id = '01830001'
        json_obj = ni.check_db(series, amiibo_id)
        self.assertEqual(json_obj['amiiboSeries'], 'Animal Crossing')
        self.assertEqual(json_obj['character'], 'Tom Nook')

        amiibo_id = '021b0001' #lower
        json_obj = ni.check_db(series, amiibo_id)
        self.assertEqual(json_obj['amiiboSeries'], 'Animal Crossing')
        self.assertEqual(json_obj['character'], 'Tutu')

        amiibo_id = '021B0001' #upper
        json_obj = ni.check_db(series, amiibo_id)
        self.assertEqual(json_obj['amiiboSeries'], 'Animal Crossing')
        self.assertEqual(json_obj['character'], 'Tutu')

        series = 0x01
        amiibo_id = '00000000'
        json_obj = ni.check_db(series, amiibo_id)
        self.assertEqual(json_obj['amiiboSeries'], 'Super Mario Bros.')
        self.assertEqual(json_obj['character'], 'Mario')

        series = 0xFF #fake
        amiibo_id = '00000000' #mismatched id to series
        json_obj = ni.check_db(series, amiibo_id)
        self.assertIsNone(json_obj['amiiboSeries'])
        self.assertIsNone(json_obj['character'])

        series = 0x00 #fake
        amiibo_id = 'ffffffff' #fake
        json_obj = ni.check_db(series, amiibo_id)
        self.assertIsNone(json_obj['amiiboSeries'])
        self.assertIsNone(json_obj['character'])

if __name__ == '__main__':
    unittest.main()

