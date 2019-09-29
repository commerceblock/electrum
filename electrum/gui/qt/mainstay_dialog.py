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

import socket

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
import PyQt5.QtCore as QtCore

from electrum.i18n import _
from electrum import constants
from electrum.util import print_error
from electrum.network import serialize_server, deserialize_server

from .util import *
from .network_dialog import NodesListWidget, TorDetector

protocol_names = ['TCP', 'SSL']
protocol_letters = 'ts'

class MainstayDialog(QDialog):
    def __init__(self, network, config, network_updated_signal_obj, network_btc, mainstay_thread):
        QDialog.__init__(self)
        self.setWindowTitle(_('Mainstay'))
        self.setMinimumSize(500, 20)
        self.nlayout = MainstayLayout(network, config, False, network_btc, mainstay_thread)
        self.network_updated_signal_obj = network_updated_signal_obj
        vbox = QVBoxLayout(self)
        vbox.addLayout(self.nlayout.layout())
        vbox.addLayout(Buttons(CloseButton(self)))
        self.network_updated_signal_obj.network_updated_signal.connect(
            self.on_update)
        network.register_callback(self.on_network, ['updated', 'interfaces'])

    def on_network(self, event, *args):
        self.network_updated_signal_obj.network_updated_signal.emit(event, args)

    def on_update(self):
        self.nlayout.update()


class MainstayLayout(object):

    def __init__(self, network, config, wizard=False, network_btc=None, mainstay_thread=None):
        self.network = network
        self.network_btc = network_btc
        self.mainstay_thread = mainstay_thread
        self.config = config
        self.protocol = None
        self.tor_proxy = None

        self.tabs = tabs = QTabWidget()
        mainstay_tab = QWidget()
        network_tab = QWidget()
        tabs.addTab(mainstay_tab, _(' Mainstay '))
        tabs.addTab(network_tab, _(' Bitcoin Network '))

        # network tab
        grid = QGridLayout(network_tab)
        grid.setSpacing(8)

        self.btc_server_host = QLineEdit()
        self.btc_server_host.setFixedWidth(200)
        self.btc_server_port = QLineEdit()
        self.btc_server_port.setFixedWidth(60)
        self.autoconnect_btc = QCheckBox(_('Select Bitcoin server automatically'))
        self.autoconnect_btc.setEnabled(self.config.is_modifiable('btc_auto_connect'))

        self.btc_server_host.editingFinished.connect(self.set_btc_server)
        self.btc_server_port.editingFinished.connect(self.set_btc_server)
        self.autoconnect_btc.clicked.connect(self.set_btc_server)
        self.autoconnect_btc.clicked.connect(self.update)

        msg = ' '.join([
            _("If auto-connect is enabled, the transaction server used will correspond to the longest blockchain."),
            _("If it is disabled, you have to choose a server you want to use. Ocean wallet will warn you if your server is lagging.")
        ])
        grid.addWidget(self.autoconnect_btc, 2, 0, 1, 3)
        grid.addWidget(HelpButton(msg), 2, 4)

        grid.addWidget(QLabel(_('Server') + ':'), 3, 0)
        grid.addWidget(self.btc_server_host, 3, 1, 1, 2)
        grid.addWidget(self.btc_server_port, 3, 3)

        self.split_label = QLabel('')
        grid.addWidget(self.split_label, 5, 0, 1, 3)

        self.btc_nodes_list_widget = NodesListWidget(self)
        grid.addWidget(self.btc_nodes_list_widget, 7, 0, 1, 5)

        grid.setRowStretch(7, 1)

        # Blockchain Tab
        grid = QGridLayout(mainstay_tab)

        self.mainstay_url = QLineEdit()
        self.mainstay_url.setFixedWidth(270)
        self.mainstayon = QCheckBox(_('Enable Mainstay'))
        self.mainstayon.setEnabled(self.config.is_modifiable('mainstay_on'))

        self.mainstay_url.editingFinished.connect(self.set_mainstay_url)
        self.mainstayon.clicked.connect(self.set_mainstay_url)
        self.mainstayon.clicked.connect(self.update)

        msg = ' '.join([
            _("Enabling Mainstay confirmations connects to the Bitcoin network and the Mainstay service. "),
            _("This feature provides in-wallet SPV validation of the immutability of the picoChain. ")
        ])

        grid.addWidget(self.mainstayon, 0, 0, 1, 3)
        grid.addWidget(HelpButton(msg), 0, 4)

        msg = _("This is the URL of the Mainstay connector service to retrieve slot-proofs")
        grid.addWidget(QLabel(_('Connector URL') + ':'), 1, 0)
        grid.addWidget(self.mainstay_url, 1, 1, 1, 2)
        grid.addWidget(HelpButton(msg), 1, 4)

        if self.network_btc and self.mainstay_thread:

            msg = _("This is the base transaction ID of the Bitcoin staychain committed to the picoChain genesis block.")
            self.mainstay_base = QLineEdit()
            self.mainstay_base.setFixedWidth(270)
            self.mainstay_base.setText(self.mainstay_thread.base)
            self.mainstay_base.setReadOnly(True)
            self.mainstay_base.setCursorPosition(0);
            self.mainstay_base.setStyleSheet("color: rgb(90, 90, 90); background: rgb(210, 210, 210)")
            grid.addWidget(QLabel(_('Staychain base') + ':'), 2, 0)
            grid.addWidget(self.mainstay_base, 2, 1, 1, 2)
            grid.addWidget(HelpButton(msg), 2, 4)

            msg =  _("This is the staychain slot ID committed to the picoChain genesis block")
            self.slot_label = QLabel(str(self.mainstay_thread.slot))
            grid.addWidget(QLabel(_('Slot ID') + ':'), 3, 0)
            grid.addWidget(self.slot_label, 3, 1, 1, 3)
            grid.addWidget(HelpButton(msg), 3, 4)

            grid.addWidget(QLabel(''), 5, 0)
            bclabel = QLabel(_('Bitcoin'))
            pclabel = QLabel(_(constants.net.WALLETTITLE+' chain'))
            bclabel.setAlignment(Qt.AlignCenter)
            pclabel.setAlignment(Qt.AlignCenter)
            grid.addWidget(bclabel, 6, 0)
            grid.addWidget(QLabel(_(' ')), 6, 1)
            grid.addWidget(pclabel, 6, 2)

            msg =  _("Connection status of the Bitcoin blockchain and the "+constants.net.WALLETTITLE+" chain")
            self.btc_status_label = QLabel('')
            self.btc_status_label.setAlignment(Qt.AlignCenter)
            self.status_label = QLabel('')
            self.status_label.setAlignment(Qt.AlignCenter)
            grid.addWidget(self.btc_status_label, 7, 0)
            conlabel = QLabel(_('-  Connection  -'))
            conlabel.setAlignment(Qt.AlignCenter)
            conlabel.setStyleSheet('color: rgb(90, 90, 90)')
            grid.addWidget(conlabel, 7, 1)
            grid.addWidget(self.status_label, 7, 2)        

            msg =  _("The heights of the local verified Bitcoin blockchain and the "+constants.net.WALLETTITLE+" chain")
            self.btc_height_label = QLabel('')
            self.btc_height_label.setAlignment(Qt.AlignCenter)
            self.height_label = QLabel('')
            self.height_label.setAlignment(Qt.AlignCenter)
            grid.addWidget(self.btc_height_label, 8, 0)
            hlabel = QLabel(_('-  Height  -'))
            hlabel.setAlignment(Qt.AlignCenter)
            hlabel.setStyleSheet('color: rgb(90, 90, 90)')
            grid.addWidget(hlabel, 8, 1)
            grid.addWidget(self.height_label, 8, 2)
            grid.addWidget(HelpButton(msg), 8, 4)        

            msg =  _("The height of the latest Bitcoin attestation and the committed the "+constants.net.WALLETTITLE+" chain height")
            self.btc_attest_height_label = QLabel('')
            self.btc_attest_height_label.setAlignment(Qt.AlignCenter)
            self.attest_height_label = QLabel('')
            self.attest_height_label.setAlignment(Qt.AlignCenter)
            alabel = QLabel(_('-  Attested  -'))
            alabel.setAlignment(Qt.AlignCenter) 
            alabel.setStyleSheet('color: rgb(90, 90, 90)')           
            grid.addWidget(self.btc_attest_height_label, 9, 0)
            grid.addWidget(alabel, 9, 1)
            grid.addWidget(self.attest_height_label, 9, 2)
            grid.addWidget(HelpButton(msg), 9, 4)

#            grid.setRowStretch(10, 1)

        else:
            grid.setRowStretch(2, 1)



        vbox = QVBoxLayout()
        vbox.addWidget(tabs)
        self.layout_ = vbox

        self.update()

    def enable_set_server(self):
        if self.config.is_modifiable('btc_server'):
            enabled = not self.autoconnect_btc.isChecked()
            self.btc_server_host.setEnabled(enabled)
            self.btc_server_port.setEnabled(enabled)
        else:
            for w in [self.autoconnect_btc, self.btc_server_host, self.btc_server_port]:
                w.setEnabled(False)

    def enable_mainstay_url(self):
        if self.config.is_modifiable('mainstay_url'):
            enabled = self.mainstayon.isChecked()
            self.mainstay_url.setEnabled(enabled)
        else:
            for w in [self.mainstayon, self.mainstay_url]:
                w.setEnabled(False)

    def update(self):

        if self.network_btc:
            host, port, protocol, proxy_config, auto_connect = self.network.get_parameters()
            host_btc, port_btc, protocol_btc, proxy_config_btc, auto_connect_btc, oneserver = self.network_btc.get_parameters()
            self.btc_server_host.setText(host_btc)
            self.btc_server_port.setText(port_btc)        
            self.autoconnect_btc.setChecked(auto_connect_btc)

        self.mainstay_url.setText(self.network.mainstay_server)
        self.mainstayon.setChecked(self.network.mainstay_on)

        self.enable_mainstay_url()

        if self.network_btc and self.mainstay_thread:

            height_str = str(self.network.get_local_height())
            self.height_label.setText(height_str)
            n = len(self.network.get_interfaces())
            status = _("{0} nodes").format(n)
            self.status_label.setText(status)

            btc_height_str = str(self.network_btc.get_local_height())
            self.btc_height_label.setText(btc_height_str)
            n = len(self.network_btc.get_interfaces())
            btc_status = _("{0} nodes").format(n)
            self.btc_status_label.setText(btc_status)

            self.btc_nodes_list_widget.update(self.network_btc)

            if self.mainstay_thread.synced:
                self.btc_attest_height_label.setText(str(self.mainstay_thread.btc_height))
                self.attest_height_label.setText(str(self.mainstay_thread.height))

    def layout(self):
        return self.layout_

    def change_protocol(self, use_ssl):
        p = 's' if use_ssl else 't'
        host = self.server_host.text()
        pp = self.servers.get(host, constants.net.DEFAULT_PORTS)
        if p not in pp.keys():
            p = list(pp.keys())[0]
        port = pp[p]
        self.server_host.setText(host)
        self.server_port.setText(port)
        self.set_protocol(p)
        self.set_server()

    def accept(self):
        pass

    def set_btc_server(self):
        if self.network_btc:
            host, port, protocol, proxy, auto_connect, oneserver = self.network_btc.get_parameters()
            host = str(self.btc_server_host.text())
            port = str(self.btc_server_port.text())
            auto_connect = self.autoconnect_btc.isChecked()
            self.network_btc.set_parameters(host, port, protocol, proxy, auto_connect)

    def set_mainstay_url(self):
        mainstay_url = str(self.mainstay_url.text())
        mainstay_on = self.mainstayon.isChecked()
        self.network.set_mainstay_url(mainstay_url,mainstay_on)
