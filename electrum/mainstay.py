from datetime import datetime
import inspect
import requests
import sys
import os
import json
from threading import Thread
import time
import csv
import decimal
from decimal import Decimal

from .bitcoin import COIN, CKD_pub, hash160_to_b58_address, rev_hex
from .transaction import BTCTransaction, parse_redeemScript_multisig, multisig_script
from .crypto import hash_160
from .verifier import SPV
from . import constants
from .i18n import _
from .util import PrintError, ThreadJob, make_dir, bh2u, bfh

class MainstayThread(ThreadJob):

    def __init__(self, config, network, btc_network):
        self.config = config
        self.network = network
        self.btc = btc_network
        self.url = self.network.mainstay_server
        genesis = self.network.blockchain().read_header(0)
        self.tip = genesis.get('attestation_hash')
        self.slot = 2
        self.script = constants.net.MAINSTAY_SCRIPT
        self.chaincodes = constants.net.MAINSTAY_CHAINCODES
        self.base_pubkeys = parse_redeemScript_multisig(bytes.fromhex(self.script))[3]
        if len(self.base_pubkeys) != len(self.chaincodes): self.print_error("mainstay error: incorrect number of chaincodes")
        self.staychain = []
        self.height = 0
        self.synced = False
        self.verify_full_staychain = False
        self.load_staychain()
        self.timeout = 0


    def path(self):
        d = util.get_headers_dir(self.config)
        filename = 'staychain'
        return os.path.join(d, filename)

    def staychain_sync(self):
        #staychin is array of verified links in order of most recent commitment first
        #link format: BTC blockheight : staychain TxID : commitment ; sidechain blockheight : proof path
        #get the staychain tip
        top_proof = self.get_latest_slot_proof()
        txid = top_proof['response']['txid']
        if txid == self.tip:
            self.synced = True
            return True
        txraw = self.btc.get_transaction(txid)
        tx = BTCTransaction(txraw)
        #verify
        if self.verify_p2c_commitment(top_proof, tx) and self.verify_slot_proof(top_proof):
            btc_height = self.verify_btc_tx_path(top_proof, tx, txid)
            if not btc_height:
                self.print_error("staychain top proof failed: ", txid)
                self.synced = False
                return False
        else:
            self.print_error("staychain top proof failed: ", txid)
            self.synced = False
            return False
        #find the top height
        chaintip = self.network.get_local_height()
        for h in range(chaintip,0,-1):
            block_hash = self.network.blockchain().get_hash(h)
            if top_proof['response']['commitment'] == block_hash:
                top_link.append(h)
                break
        if h == 0: 
            self.print_error("init staychain commitment not in sidechain")
            return False
        top_link = []
        top_link.append(btc_height)
        top_link.append(top_proof['response']['txid'])
        top_link.append(top_proof['response']['commitment'])
        top_link.append(top_proof['response']['ops'])
        self.staychain.append(top_link)
        self.tip = txid
        #then move down the staychain verifying the proofs as we go
        scan = True
        while scan:
            txid = tx.inputs()[0]['prevout_hash']
            #when the staychain reaches the root commitment, syncing is complete
            if txid == self.tip:
                self.synced = True
                return True
            #check for signgle output
            txraw = self.btc.get_transaction(txid)
            tx = BTCTransaction(txraw)
            script_addr = tx.outputs()[0][1]
            addr_info = self.btc.get_address_history(script_addr)
            for txh in addr_info:
                if txh['tx_hash'] == txid: tx_height = txh['height']


            if self.verify_full_staychain:
                attestation = self.get_attestation(txid)
                m_root = attestation["response"]["attestation"]["merkle_root"]
                proof = self.get_slot_proof(m_root)
                if self.verify_p2c_commitment(top_proof, tx) and self.verify_slot_proof(top_proof):
                    btc_height = self.verify_btc_tx_path(top_proof, tx, txid)
                    if not btc_height: 
                        self.print_error("staychain SPV failed: ", txid)
                        return False
                else:
                    self.print_error("staychain proof failed: ", txid)
                    return False
                commit = proof['response']['commitment']
                link = []
                link.append(tx_height)
                link.append(txid) 
                link.append(commit)
                hi = h
                for hi in range(h,0,-1):
                    block_hash = self.network.blockchain().get_hash(h)
                    if commit == block_hash:
                        link.append(h)
                        break
                link.append(proof['response']['ops'])
            else:
                link = []
                link.append(tx_height)
                link.append(txid)
                link.append(None)
                link.append(None)
                link.append(None)
                self.staychain.append(link)
        return None

    def load_staychain(self):
        #load in the staychain from file
        #if file not there, then initialise the staychain
        try:
            with open(self.path(), 'r') as f:
                r = json.loads(f.read())
        except:
            r = {}
        self.staychain = r
        try:
            self.tip = self.staychain[-1][1]
            self.height = self.staychain[-1][0]
        except:
            self.tip = 0

    def get_mainstay_api(self, rstring):
        try:
            r = requests.request('GET', self.url+rstring, timeout=2)
            r.raise_for_status()
            proof = r.json()
            self.getms = 'connected'
            return proof
        except requests.exceptions.HTTPError as errh:
            self.print_error("get proof http error")
            self.getms = 'http_error'
            return
        except requests.exceptions.ConnectionError as errc:
            self.print_error("get proof connection error")
            self.getms = 'connection_error'
            return
        except requests.exceptions.Timeout as errt:
            self.print_error("get proof timeout error")
            self.getms = 'timeout_error'
            return
        except requests.exceptions.RequestException as err:
            self.print_error("get proof reques exception error")
            self.getms = 'request_exception'
            return
        return None

    def get_latest_slot_proof(self):
        rstring = "/api/v1/commitment/latestproof?position="+str(self.slot)
        return self.get_mainstay_api(rstring)

    def get_slot_proof(self, merkle_root):
        rstring = "/api/v1/commitment/proof?position="+str(self.slot)+"&merkle_root="+merkle_root
        return self.get_mainstay_api(rstring)

    def get_attestation(self, txid):
        rstring = "/api/v1/attestation?txid="+str(txid)
        return self.get_mainstay_api(rstring)

    def connect_to_staychain(self, tx):
        return True

    def get_path_from_commitment(self, com):
        path_size = 16
        child_size = 2
        if len(com) != path_size*child_size:
            self.print_error("commitment incorrect size for derivation path ", str(len(com)))
            return None
        derivation_path = []
        for it in range(path_size):
            index = com[it*child_size:it*child_size+child_size]
            derivation_path.append(index)
        return derivation_path

    def tweak_script(self, path):
        tweaked_keys = []
        for ikey in range(len(self.base_pubkeys)):
            cK = bytes.fromhex(self.base_pubkeys[ikey])
            c = bytes.fromhex(self.chaincodes[ikey])
            for index in path:
                cK, c = CKD_pub(cK, c, int.from_bytes(index,'big'))
            tweaked_keys.append(bh2u(cK))
        m,n,_,_,_ = parse_redeemScript_multisig(bytes.fromhex(self.script))
        tweaked_script = multisig_script(tweaked_keys, m)
        return hash160_to_b58_address(hash_160(bytes.fromhex(tweaked_script)), 5)

    def verify_p2c_commitment(self, proof, tx):
        #verify the pay-to-contract proof merkle root in the Bitcoin transaction
        script_addr = tx.outputs()[0][1]
        if len(tx.outputs()) != 1:
            self.print_error("staychain bifurcation")
            return False
        commitment = proof['response']['merkle_root']
        commitment_path = self.get_path_from_commitment(bytes.fromhex(rev_hex(commitment)))
        tweaked_addr = self.tweak_script(commitment_path)
        if script_addr == tweaked_addr:
            return True
        else:
            self.print_error("staychain address commitment verification failure")
            return False

    def verify_slot_proof(self, proof):
        #verify the Merkle path of the slot proof
        calculated_proof_root = SPV.hash_merkle_root([pth['commitment'] for pth in proof['response']['ops']], proof['response']['commitment'], self.slot)
        if calculated_proof_root == proof['response']['merkle_root']:
            return True
        else:
            self.print_error("slot proof verification failure")
            return False

    def verify_btc_tx_path(self, proof, tx, txid):
        #verify the inclusion the proof transaction in the Bitcoin blockchain via SPV
        #returns the Bitcoin block hash and height. 
        script_addr = tx.outputs()[0][1]
        addr_info = self.btc.get_address_history(script_addr)
        for txh in addr_info:
            if txh['tx_hash'] == txid: tx_height = txh['height']
        merkle_proof = self.btc.get_merkle_for_transaction(txid, tx_height)    
        calculated_merkle_root = SPV.hash_merkle_root(merkle_proof["merkle"], txid, merkle_proof["pos"])
        conf_header = self.btc.blockchain().read_header(tx_height)
        if calculated_merkle_root == conf_header.get('merkle_root'):
            return tx_height
        else:
            self.print_error("invalid SPV proof for mainstay commitment")
            return 0

    def run(self):
        #check mainstay API for new proofs every minute
        if self.timeout <= time.time():
            self.timeout = time.time() + 60
            h1 = self.network.get_local_height()
            print(h1)
            h2 = self.btc.get_local_height()
            print(h2)
