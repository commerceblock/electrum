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
import copy
import datetime
import json
import traceback

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import qrcode
from qrcode import exceptions

from electrum.bitcoin import base_encode
from electrum.i18n import _
from electrum.plugin import run_hook
from electrum import simple_config

from electrum.util import bfh
from electrum.transaction import SerializationError

from .util import *


SAVE_BUTTON_ENABLED_TOOLTIP = _("Save transaction offline")
SAVE_BUTTON_DISABLED_TOOLTIP = _("Please sign this transaction in order to save it")


dialogs = []  # Otherwise python randomly garbage collects the dialogs...


def show_tx_list(tx_list, parent):
    try:
        d = TxListDialog(tx_list, parent)
    except SerializationError as e:
        traceback.print_exc(file=sys.stderr)
        parent.show_critical(_("Ocean wallet was unable to deserialize the transaction list:") + "\n" + str(e))
    else:
        dialogs.append(d)
        d.exec_()
#        d.show()


class TxListDialog(QDialog, MessageBoxMixin):

    def __init__(self, tx_list, parent):
        '''Transactions in the wallet will show their description.
        Pass desc to give a description for txs not yet in the wallet.
        '''
        # We want to be a top-level window
        QDialog.__init__(self, parent=None)
        # Take a copy; it might get updated in the main window by
        # e.g. the FX plugin.  If this happens during or after a long
        # sign operation the signatures are lost.
        self.tx_list = tx_list = copy.deepcopy(tx_list)
        self.main_window = parent
        self.wallet = parent.wallet
        self.saved = False

        self.setMinimumWidth(450)
        self.setWindowTitle(_("Transaction List"))

        vbox = QVBoxLayout()
        self.setLayout(vbox)

        vbox.addWidget(QLabel(_("Number of trasactions:")))

        self.tx_count_label = QLabel()
        vbox.addWidget(self.tx_count_label)
        self.amount_label = QLabel()
        vbox.addWidget(self.amount_label)
        self.address_label = QLabel()
        vbox.addWidget(self.address_label)

        self.tx_count_label.setText(_('No. transactions:') + ' ' + str(len(self.tx_list)))

        amount = 0
        for tx in self.tx_list:
            addr, v, a = tx.get_outputs()[0]
            amount += v

        self.amount_label.setText(_('Total value:') + ' ' + str(round(amount/100000000,8)))

        self.address_label.setText(_('Payment address:') + ' ' + addr)

        tx_hash, status, label, can_broadcast, can_rbf, amount, fee, height, conf, timestamp, exp_n = self.wallet.get_tx_info(self.tx_list[0])

        self.status_label = QLabel()
        self.status_label.setText(_('Status:')+' '+status)
        vbox.addWidget(self.status_label)

        vbox.addStretch(1)

        self.sign_button = b = QPushButton(_("Sign all"))
        b.clicked.connect(self.sign)

        self.broadcast_button = b = QPushButton(_("Broadcast all"))
        b.clicked.connect(self.do_broadcast)

        self.export_button = b = QPushButton(_("Export list"))
        b.clicked.connect(self.export)

        self.cancel_button = b = QPushButton(_("Close"))
        b.clicked.connect(self.close)
        b.setDefault(True)

        # Action buttons
        self.buttons = [self.sign_button, self.broadcast_button, self.cancel_button]
        # Transaction sharing buttons
        self.sharing_buttons = [self.export_button]

        run_hook('transaction_dialog', self)

        hbox = QHBoxLayout()
        hbox.addLayout(Buttons(*self.sharing_buttons))
        hbox.addStretch(1)
        hbox.addLayout(Buttons(*self.buttons))
        vbox.addLayout(hbox)
        self.update()

    def do_broadcast(self):
        self.main_window.push_top_level_window(self)
        try:
            self.main_window.broadcast_transaction_list(self.tx_list)
        finally:
            self.main_window.pop_top_level_window(self)
        self.saved = True

    def sign(self):
        def sign_done(success):
            # note: with segwit we could save partially signed tx, because they have a txid
            tx_hash, status, label, can_broadcast, can_rbf, amount, fee, height, conf, timestamp, exp_n = self.wallet.get_tx_info(self.tx_list[0])

            self.status_label.setText(_('Status:')+' '+status)
            self.update()
            self.main_window.pop_top_level_window(self)

        self.sign_button.setDisabled(True)
        self.main_window.push_top_level_window(self)
        self.main_window.sign_tx_list(self.tx_list, sign_done)

    def export(self):
        name = 'signed_list.txns' if self.tx_list[0].is_complete() else 'unsigned.txns'
        fileName = self.main_window.getSaveFileName(_("Select where to save the signed transaction list"), name, "*.txns")
        if fileName:
            with open(fileName, "w+") as f:
                tx_vec = []
                for tx in self.tx_list:
                    tx_vec.append(tx.as_dict())
                f.write(json.dumps(tx_vec, indent=4) + '\n')
            self.show_message(_("Transaction list exported successfully"))
            self.saved = True
