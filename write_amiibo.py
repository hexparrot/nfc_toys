#!/usr/bin/env python3
__author__ = "William Dizon"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "William Dizon"
__email__ = "wdchromium@gmail.com"
__status__ = "Development"

import nfc
from easy_nfc import nfc_parser
from amiibo import AmiiboDump, AmiiboMasterKey, crypto

lock_data = [#page, #byteoffset, #bytedata
    ('82h', 3, [0x01, 0x00, 0x0F, 0xBD]), #dynamic lockpages
    ('02h', 2, [0x0F, 0x48, 0x0F, 0xE0]), #static lockpages
]

ni = nfc_parser()

with open('unfixed-info.bin', 'rb') as fp_d, open('locked-secret.bin', 'rb') as fp_t:
    master_keys = AmiiboMasterKey.from_separate_bin(fp_d.read(), fp_t.read())

with open('orig.bin', 'rb') as fp:
    dump = AmiiboDump(master_keys, fp.read())

try:
    dump.unlock()
except amiibo.crypto.AmiiboHMACDataError:
    print('AmiiboHMACDataError error thrown (corrupt bin?)')
    quit(1)
else:
    print(ni)
    dump.uid_hex = ni.spaced_hex(ni.uid)
    dump.lock()
    dump.unset_lock_bytes()

    with open('dump.bin', 'wb') as fp:
        fp.write(dump.data)

    ni.commit_image(byte_override=lock_data)

