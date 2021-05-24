# nfc_toys
a high-level interface for reading and writing nfc toys

## Built for use with nfcpy

List of supported devices: https://nfcpy.readthedocs.io/en/latest/overview.html#supported-devices

NFCPY may require administrative changes to your udev configuration to operate. Use the following
line to detect and troubleshoot operation in your *nix environment.

`$ python3 -m nfc --search-tty`

### Amiibo usage
```
$ pip3 install nfcpy
$ pip3 install pyamiibo
$ wget [url for unfixed-info.bin]
$ wget [url for locked-secret.bin]
$ wget [url for amiibo.json]

$ cp [some_amiibo_dump.bin] orig.bin
$ write_amiibo.py
```

### Troubleshooting setup

```
# python3 -m nfc --search-tty
This is the 1.0.3 version of nfcpy run in Python 3.7.3
I'm now searching your system for contactless devices
** found usb:054c:06c1 at usb:001:004 but it's already used
-- scan sysfs entry at '/sys/bus/usb/devices/1-1:1.0/'
-- the device is used by the 'port100' kernel driver
-- this kernel driver belongs to the linux nfc subsystem
-- you can remove it to free the device for this session
   sudo modprobe -r port100
-- and blacklist the driver to prevent loading next time
   sudo sh -c 'echo blacklist port100 >> /etc/modprobe.d/blacklist-nfc.conf'
Sorry, but I couldn't find any contactless device
# sudo modprobe -r port100
# python3 -m nfc --search-tty
This is the 1.0.3 version of nfcpy run in Python 3.7.3
I'm now searching your system for contactless devices
** found SONY RC-S380/S NFC Port-100 v1.11 at usb:001:004
```
