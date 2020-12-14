#!/usr/bin/env python
#
# Electrum - lightweight Ocean client
# Copyright (C) 2012 thomasv@gitorious
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

from electrum.i18n import _

from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton

from .util import WindowModalDialog, ButtonsLineEdit, ColorScheme, Buttons, CloseButton
from electrum.transaction import Transaction, TxOutput, TYPE_SCRIPT
from electrum import constants
from .history_list import HistoryList
from .qrtextedit import ShowQRTextEdit
import operator
import json

MAX_INPUTS = 20

class ConsolidateDialog(WindowModalDialog):

    def __init__(self, parent, coins, address):
        WindowModalDialog.__init__(self, parent, _("Consolidate Address"))
        self.address = address
        self.parent = parent
        self.config = parent.config
        self.wallet = parent.wallet
        self.app = parent.app
        self.saved = True
        self.coins = coins

        self.setMinimumWidth(500)
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        vbox.addWidget(QLabel(_("Address from:")))
        self.addr_e = ButtonsLineEdit(self.address)
        self.addr_e.setReadOnly(True)
        vbox.addWidget(self.addr_e)

        send_to = self.wallet.get_unused_address()

        vbox.addWidget(QLabel(_("Address to:")))
        self.addr_e = ButtonsLineEdit(send_to)
        self.addr_e.setReadOnly(True)
        vbox.addWidget(self.addr_e)

        total = len(self.coins)

        assets = {}
        txis = []
        # sort coins into assets
        self.coins.sort(key=operator.itemgetter('asset'))

        #split coins by assets into buckets
        num_assets = 0
        start_asset = self.coins[0]["asset"]
        templist = []
        n = 0
        for i,coin in enumerate(self.coins):
            self.wallet.add_input_info(coin)
            if coin["asset"] in assets:
                assets[coin["asset"]] += 1
            else:
                assets[coin["asset"]] = 1

            if start_asset == coin["asset"]:
                n += 1
                templist.append(coin)
                if n % MAX_INPUTS == 0:
                    txis.append(templist)
                    templist = []
                    n = 0
                    if i == len(self.coins) - 1: break
                if i == len(self.coins) - 1:
                    txis.append(templist)
                    break
            else:
                txis.append(templist)
                templist = []
                templist.append(coin)               
                n = 1
                start_asset = coin["asset"]

        self.txns = []
        # create unsigned transactions
        fee_estimator = self.config.get('fixed_fee', constants.net.FIXEDFEE)

        contr = constants.net.CONTRACT2HASH
        op_return_script = '6a20' + "".join(reversed([contr[i:i+2] for i in range(0, len(contr), 2)]))

        for tx_inputs in txis:
            asset = tx_inputs[0]["asset"]
            value = 0
            for coin in tx_inputs:
                value += coin["value"]
            outputs = [TxOutput(0, send_to, value - fee_estimator,1,asset,1)]
            outputs.append(TxOutput(TYPE_SCRIPT,'',fee_estimator,1,asset,1))
            outputs.append(TxOutput(TYPE_SCRIPT,op_return_script,0,1,asset,1))

            tx = Transaction.from_io(tx_inputs, outputs[:])
            self.txns.append(tx)

        vbox.addWidget(QLabel(_("Total outputs:")))
        self.addr_e = ButtonsLineEdit(str(total))
        self.addr_e.setReadOnly(True)
        vbox.addWidget(self.addr_e)

        vbox.addWidget(QLabel(_("Total assets:")))
        self.addr_e = ButtonsLineEdit(str(len(assets)))
        self.addr_e.setReadOnly(True)
        vbox.addWidget(self.addr_e)

        vbox.addWidget(QLabel(_("Transactions:")))
        self.addr_e = ButtonsLineEdit(str(len(self.txns)))
        self.addr_e.setReadOnly(True)
        vbox.addWidget(self.addr_e)

        self.export_button = b = QPushButton(_("Export"))
        b.clicked.connect(self.export)

        vbox.addLayout(Buttons(self.export_button))
        vbox.addLayout(Buttons(CloseButton(self)))

    def export(self):
        name = 'unsigned_list'
        fileName = self.parent.getSaveFileName(_("Select where to save the transaction list"), name, "*.txns")
        if fileName:
            with open(fileName, "w+") as f:
                tx_vec = []
                for tx in self.txns:
                    tx_vec.append(tx.as_dict())
                f.write(json.dumps(tx_vec, indent=4) + '\n')
            self.show_message(_("Transaction list exported successfully"))
