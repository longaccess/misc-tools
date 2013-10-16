#! /usr/bin/env python

# Decrypt an archive downloaded from longaccess.com
# Example cat archive | decrypt.py archive_key_in_base64 > archive.zip

import Crypto.Cipher.AES
import Crypto.Util.Counter
from base64 import b64decode
import sys

key = b64decode(sys.argv[1])
encrypted = sys.stdin.read()

BLOCKSIZE = 16
ctr = Crypto.Util.Counter.new(128, prefix='', initial_value=0L)
cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CTR, counter=ctr)
decrypted = cipher.decrypt(encrypted)
num = ord(decrypted[-1])

sys.stdout.write(decrypted[0:-num])
