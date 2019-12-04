
from kivy.factory import Factory

from electrum.util import print_error


class KycRegisterDialog(Factory.Popup):
    kvname = 'kyc_register'
    
    def init(self, kyckey):
        self.ids['kyc_key'].text = kyckey



