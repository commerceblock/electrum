# -*- coding: utf-8 -*-
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2018 The Electrum developers
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import json
#from electrum import bitcoin
#from .bitcoin import *


def read_json(filename, default):
    path = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(path, 'r') as f:
            r = json.loads(f.read())
    except:
        r = default
    return r

class AbstractNet:

    @classmethod
    def max_checkpoint(cls) -> int:
        return max(0, len(cls.BTC_CHECKPOINTS) * 2016 - 1)

class OceanMainnet(AbstractNet):

    TESTNET = False
    FIXEDFEE = 50000
    SHOWFX = False
    WALLETPATH = "dgldwallet"
    WALLETTITLE = "DGLD Wallet"
    CONTRACTINTX = True
    BASIC_HEADER_SIZE = 172
    MIN_HEADER_SIZE = 176
    WIF_PREFIX = 0xB4
    ADDRTYPE_P2PKH = 38
    ADDRTYPE_P2SH = 97
    SEGWIT_HRP = "bc"
    GENESIS = "c66cb6eb7cd585788b294be28c8dcd6be4e37a0a6d238236b11c0beb25833bb9"
    DEFAULT_PORTS = {'t': '50001', 's': '50002'}
    DEFAULT_SERVERS = read_json('servers.json', {})
    MAPPING_URL = 'https://s3.eu-west-1.amazonaws.com/gtsa-mapping/map.json'
    CHECKPOINTS = []    # no handling for checkpoins

    MAINSTAY_URL = 'https://mainstay.xyz'
    MAINSTAY_SCRIPT = "522103639a65bfb3dd5a579e65231a4e70327aba358e956d6e10f7ea2e25dd631e4d6621024f714a1b93697c5a3865259ac3a865bb306e8b720c3bec46bae3298ef3fa796421035ea174407b61b85fc83993084c471f78095779737a75adf2a2e52cdd2a36edd353ae"
    MAINSTAY_CHAINCODES = ["8c57ec95db9ddab3b17ea5ae8c1411bbc0859d1a5262ff67d475cc880e14cfd9","087c28f8989d4a5e692127dbaeffc86b7d2d44b878b3a585b2c98967c854ed8d","2f94eeb596c3c7d9a5746b17150412a3c5f4f9f999ffb2395fc59a14bcfc4271"]
    MAINSTAY_SLOT = 1
    BTC_GENESIS = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
    BTC_DEFAULT_SERVERS = read_json('btc_servers.json', {})
    BTC_CHECKPOINTS = read_json('btc_checkpoints.json', [])

    XPRV_HEADERS = {
        'standard':    0x0488ade4,  # xprv
        'p2wpkh-p2sh': 0x049d7878,  # yprv
        'p2wsh-p2sh':  0x0295b005,  # Yprv
        'p2wpkh':      0x04b2430c,  # zprv
        'p2wsh':       0x02aa7a99,  # Zprv

    }
    XPUB_HEADERS = {
        'standard':    0x0488b21e,  # xpub
        'p2wpkh-p2sh': 0x049d7cb2,  # ypub
        'p2wsh-p2sh':  0x0295b43f,  # Ypub
        'p2wpkh':      0x04b24746,  # zpub
        'p2wsh':       0x02aa7ed3,  # Zpub

    }
    BIP44_COIN_TYPE = 0

    CONTROLER1 = "04103fda45d114931ab5b24b77a383d16c3e510ee83ebf91987436a21e02ad7b6d41dc52d40ac27a3703be934ebd207071ba83b3674ac4fc01bb602fb434eddfee"
    CONTROLER2 = "04ee4278985ac544f0fec151a1ba21ac97e26fdbf230973e07aeb608ed0a18b535396579ebfbc6a54efa7628f4c7e51cd4ed6c6e6967699d387352efa5971d6548"
    CONTROLER3 = "04d36a30f4eb8abd75550666e263dde3b302d3fce3847a53ec283b670e9a8387bfa304e4f30e8e4a2392f0c87ce040e11ad9d282c172d0ed8341c046dea9278304"
    #Address the whitelist tokens are initially paid to (defined in the genesis block)
    WHITELISTCOINSDESTINATION = "76a91464e33e58fa0a18348d94f064a09fe6ec65448ef588ac"
    WHITELISTCOINSADDRESS = "GT3NDU8J5NkBeZf6sU2UoHjc1uaiyES5Ld"
    WHITELISTASSET="d109a2432528b0a9208e7f4258f569e246c25bd0cd90f4d8160f1704be833c23"

    CHALLENGE = "5321024cc60ff6ca8423c8353142fab8b4aa8b42e66eac2ae51a7cde1eaeb54a73a31e21034878127e5f0a5c84e775d754f02bcea9393c17b7fc05a01a2c011f7a419e6f932103b7d99275aba3db614faeeba3920295e8d661a3a0a705d999b8a38aca0f8fc5d321039d1175c43f855f003fd1e980b618b3d504f2099754b8afa3667ead04b9dbb6d921027c2e025fb4d41e7c4b757a722bff6172233fa576b0aac7d5d8e4e32cfbf2a1df55ae"
    ENCRYPTED_WHITELIST=False

    
# Current Testnet purposes
class OceanTestnet(OceanMainnet):
    TESTNET = True
    DEFAULT_SERVERS = read_json('servers_testnet.json', {})
    WHITELISTASSET= "d09fe09cd516d723ed62a99d86cda67094ddefd2222f8049b6a858cee40ef94f"
    WHITELISTCOINSDESTINATION = "76a9144f33907bf3ded16fb263d01dc87cb0119732daf888ac"
    WHITELISTCOINSADDRESS = "GR4ha3BeUaMvekwX5JeDbsB54yYhPcJrRZ"
    GENESIS = "9e18c41bcffcb32e1fe3ec5f305baa61696e21fba1e570cfafc3a250013cce26"

    CHALLENGE = "532103041f9d9edc4e494b07eec7d3f36cedd4b2cfbb6fe038b6efaa5f56b9636abd7b21037c06b0c66c98468d64bb43aff91a65c0a576113d8d978c3af191e38845ae5dab21031bd16518d76451e7cf13f64087e4ae4816d08ae1d579fa6c172dcfe4476bd7da210226c839b56b99af781bbb4ce14365744253ae75ffe6f9182dd7b0df95c439537a21023cd2fc00c9cb185b4c0da16a45a1039e16709a61fb22340645790b7d1391b66055ae"


    XPRV_HEADERS = {
        'standard':    0x04358394,  # xprv
        'p2wpkh-p2sh': 0x049d7878,  # yprv
        'p2wsh-p2sh':  0x0295b005,  # Yprv
        'p2wpkh':      0x04b2430c,  # zprv
        'p2wsh':       0x02aa7a99,  # Zprv

    }

    XPUB_HEADERS = {
        'standard':    0x043587cf,  # xpub
        'p2wpkh-p2sh': 0x049d7cb2,  # ypub
        'p2wsh-p2sh':  0x0295b43f,  # Ypub
        'p2wpkh':      0x04b24746,  # zpub
        'p2wsh':       0x02aa7ed3,  # Zpub
    }

    CONTROLER1 = "048249c166d63d2b76c958bab0ad13bf7009121acfe1c2727701df8a4fc3f3d045744cf6894db9df71ce9ef64d2bb5c6d80a1318b74dfee4ad69137469defa9d2a"
    CONTROLER2 = "04441ef52d1923962e44fd86c0bc019dd768988f603d625791a721f855ddcf6320b2fad5507dc16acf4beace8658b5092b450f7c4d32b15b7351c0ef2afe7574e4"
    CONTROLER3 = "04ac8725ca6d2f68ec65ec01ae335c94d28168df07d64f66a70b7def687f2c352827ffaa540c61a4f68b0cf63c9a99fb61dccebfe7b9b0a6e75bbd4d6e5d3aba59"

    MAPPING_URL = 'https://s3.eu-west-2.amazonaws.com/cb-mapping/map.json'
    ENCRYPTED_WHITELIST=False
    
class OceanRegtest(OceanMainnet):

    TESTNET = True
    WIF_PREFIX = 0xef

    # From Ocean but never used
    #ADDRTYPE_P2PKH = 235
    #ADDRTYPE_P2SH = 75

    # Prefixes that were used for test_wallet_vertical.py case generation
    ADDRTYPE_P2PKH = 111
    ADDRTYPE_P2SH = 196

    SEGWIT_HRP = "tb"
    GENESIS = ""
    DEFAULT_PORTS = {'t': '51001', 's': '51002'}
    DEFAULT_SERVERS = read_json('servers_regtest.json', {})
    CHECKPOINTS = []

    XPRV_HEADERS = {
        'standard':    0x04358394,  # tprv
        'p2wpkh-p2sh': 0x044a4e28,  # uprv
        'p2wsh-p2sh':  0x024285b5,  # Uprv
        'p2wpkh':      0x045f18bc,  # vprv
        'p2wsh':       0x02575048,  # Vprv
    }
    XPUB_HEADERS = {
        'standard':    0x043587cf,  # tpub
        'p2wpkh-p2sh': 0x044a5262,  # upub
        'p2wsh-p2sh':  0x024289ef,  # Upub
        'p2wpkh':      0x045f1cf6,  # vpub
        'p2wsh':       0x02575483,  # Vpub
    }

    BIP44_COIN_TYPE = 1
    ENCRYPTED_WHITELIST=False
    
# don't import net directly, import the module instead (so that net is singleton)
net = OceanMainnet

def set_simnet():
    return

def set_mainnet():
    global net
    net = OceanMainnet

def set_testnet():
    global net
    net = OceanTestnet

def set_regtest():
    global net
    net = OceanRegtest
