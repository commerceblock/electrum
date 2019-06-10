from . import bitcoin
from electrum import ecc
from .util import bh2u, bfh
from .transaction import opcodes
import base64
import binascii
import hashlib
import os
import sys
                      
class RegisterAddressScript():
    def __init__(self, wallet):
        self.clear()
        self.wallet=wallet

    def finalize(self, ePubKey, ePrivKey=None) -> str:
        encrypted = ecc.ECPubkey(ePubKey).encrypt_message(self.payload, ephemeral=ePrivKey, encode=binascii.hexlify)
        return bh2u(bytes([opcodes.OP_REGISTERADDRESS])) + bitcoin.push_script_bytes(encrypted)

    def append(self, addrs):
        string_types = (str)
        string_or_bytes_types = (str, bytes)
        int_types = (int, float)
        # Base switching
        code_strings = {
            2: '01',
            10: '0123456789',
            16: '0123456789abcdef',
            32: 'abcdefghijklmnopqrstuvwxyz234567',
            58: '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz',
            256: ''.join([chr(x) for x in range(256)])
        }

        def bin_dbl_sha256(s):
            bytes_to_hash = from_string_to_bytes(s)
            return hashlib.sha256(hashlib.sha256(bytes_to_hash).digest()).digest()

        def lpad(msg, symbol, length):
            if len(msg) >= length:
                return msg
            return symbol * (length - len(msg)) + msg

        def get_code_string(base):
            if base in code_strings:
                return code_strings[base]
            else:
                raise ValueError("Invalid base!")

        def changebase(string, frm, to, minlen=0):
            if frm == to:
                return lpad(string, get_code_string(frm)[0], minlen)
            return encode(decode(string, frm), to, minlen)

        def bin_to_b58check(inp, magicbyte=0):
            if magicbyte == 0:
                inp = from_int_to_byte(0) + inp
            while magicbyte > 0:
                inp = from_int_to_byte(magicbyte % 256) + inp
                magicbyte //= 256

            leadingzbytes = 0
            for x in inp:
                if x != 0:
                    break
                leadingzbytes += 1

            checksum = bin_dbl_sha256(inp)[:4]
            return '1' * leadingzbytes + changebase(inp+checksum, 256, 58)

        def bytes_to_hex_string(b):
            if isinstance(b, str):
                return b

            return ''.join('{:02x}'.format(y) for y in b)

        def safe_from_hex(s):
            return bytes.fromhex(s)

        def from_int_representation_to_bytes(a):
            return bytes(str(a), 'utf-8')

        def from_int_to_byte(a):
            return bytes([a])

        def from_byte_to_int(a):
            return a

        def from_string_to_bytes(a):
            return a if isinstance(a, bytes) else bytes(a, 'utf-8')

        def safe_hexlify(a):
            return str(binascii.hexlify(a), 'utf-8')

        def encode(val, base, minlen=0):
            base, minlen = int(base), int(minlen)
            code_string = get_code_string(base)
            result_bytes = bytes()
            while val > 0:
                curcode = code_string[val % base]
                result_bytes = bytes([ord(curcode)]) + result_bytes
                val //= base

            pad_size = minlen - len(result_bytes)

            padding_element = b'\x00' if base == 256 else b'1' \
                if base == 58 else b'0'
            if (pad_size > 0):
                result_bytes = padding_element*pad_size + result_bytes

            result_string = ''.join([chr(y) for y in result_bytes])
            result = result_bytes if base == 256 else result_string

            return result

        def decode(string, base):
            if base == 256 and isinstance(string, str):
                string = bytes(bytearray.fromhex(string))
            base = int(base)
            code_string = get_code_string(base)
            result = 0
            if base == 256:
                def extract(d, cs):
                    return d
            else:
                def extract(d, cs):
                    return cs.find(d if isinstance(d, str) else chr(d))

            if base == 16:
                string = string.lower()
            while len(string) > 0:
                result *= base
                result += extract(string[0], code_string)
                string = string[1:]
            return result

        def b58check_to_bin(inp):
            leadingzbytes = len(re.match('^1*', inp).group(0))
            data = b'\x00' * leadingzbytes + changebase(inp, 58, 256)
            assert bin_dbl_sha256(data[:-4])[:4] == data[-4:]
            return data[1:-4]

        for addr in addrs:
            self.payload.extend(b58check_to_bin(addr))
            pubkeybytes=bfh(self.wallet.get_public_key(addr, tweaked=False))
            self.payload.extend(pubkeybytes)

    def clear(self):
        self.payload=bytearray()

    def size(self):
        return self.payload.size()
