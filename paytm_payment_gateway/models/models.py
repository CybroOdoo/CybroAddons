# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

import base64
import string
import random
import hashlib


from Crypto.Cipher import AES
from odoo.exceptions import ValidationError
from odoo import api, fields, models
from datetime import datetime
from werkzeug import urls
import hashlib
import json

import hmac
import base64

import logging

_logger = logging.getLogger(__name__)


class PaymentAcquirerAtom(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('paytm', 'Paytm')])
    paytm_merchant_id = fields.Char('Merchant ID', required_if_provider='Paytm',
                                        groups='base.group_user')
    paytm_merchant_key = fields.Char('Merchent Key', required_if_provider='Paytm',
                                        groups='base.group_user')


    @api.model
    def _get_paytm_urls(self):
        """ Atom URLS """
        return {
            'paytm_form_url':'https://securegw-stage.paytm.in/order/process'
        }


    def paytm_get_form_action_url(self):
        return self._get_paytm_urls () ['paytm_form_url']

    def paytm_form_generate_values(self ,values):
        self.ensure_one ()
        base_url=self.env ['ir.config_parameter'].sudo ().get_param ('web.base.url')
        now=datetime.now ()

        paytm_values=dict (
                          MID=self.paytm_merchant_id ,
                          ORDER_ID=str(values ['reference']) ,
                          CUST_ID = str(values.get('partner_id')),
                          INDUSTRY_TYPE_ID='Retail' ,
                          CHANNEL_ID = 'WEB',
                          TXN_AMOUNT=str(values ['amount']) ,
                          WEBSITE='WEBSTAGING',
                          EMAIL=str(values.get ('partner_email')) ,
                          MOBILE_NO = str(values.get('partner_phone')),
                          CALL_BACK_URL=urls.url_join (base_url ,'/payment/paytm/return/') ,
                          )

        paytm_values ['reqHashKey']=self.generate_checksum(paytm_values, self.paytm_merchant_key)
        return paytm_values


    def __encode__(self,to_encode ,iv ,key):
        __pad__=lambda s:s + (16 - len (s) % 16) * chr (16 - len (s) % 16)
        # Pad
        to_encode=__pad__ (to_encode)
        # Encrypt
        c=AES.new (key ,AES.MODE_CBC ,iv)
        to_encode=c.encrypt (to_encode)
        # Encode
        to_encode=base64.b64encode (to_encode)
        return to_encode.decode ("UTF-8")


    def __decode__(self,to_decode ,iv ,key):
        # Decode
        to_decode=base64.b64decode (to_decode)
        # Decrypt
        c=AES.new (key ,AES.MODE_CBC ,iv)
        to_decode=c.decrypt (to_decode)
        if type (to_decode) == bytes:
            # convert bytes array to str.
            to_decode=to_decode.decode ()
        # remove pad
        return self.__unpad__ (to_decode)


    def __id_generator__(self,size=6 ,chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
        return ''.join (random.choice (chars) for _ in range (size))


    def __get_param_string__(self,params ,escape_refund=True):
        params_string=[]
        for key in sorted (params.keys ()):
            if ("|" in params [key] or (escape_refund == True and "REFUND" in params [key])):
                respons_dict={}
                exit ()
            value=params [key]
            params_string.append ('' if value == 'null' else str (value))
        return '|'.join (params_string)


    def generate_checksum(self,param_dict ,merchant_key ,salt=None):
        params_string=self.__get_param_string__ (param_dict)
        return self.generate_checksum_by_str (params_string ,merchant_key ,salt)


    def generate_refund_checksum(self,param_dict ,merchant_key ,salt=None):
        for i in param_dict:
            if ("|" in param_dict [i]):
                param_dict={}
                exit ()
        params_string=self.__get_param_string__ (param_dict ,False)
        return self.generate_checksum_by_str (params_string ,merchant_key ,salt)


    def generate_checksum_by_str(self,param_str ,merchant_key ,salt=None):
        IV="@@@@&&&&####$$$$"
        params_string=param_str
        salt=salt if salt else self.__id_generator__ (4)
        final_string='%s|%s' % (params_string ,salt)

        hasher=hashlib.sha256 (final_string.encode ())
        hash_string=hasher.hexdigest ()

        hash_string+=salt

        return self.__encode__ (hash_string ,IV ,merchant_key)


    def verify_checksum(self,param_dict ,merchant_key ,checksum):
        # Remove checksum
        if 'CHECKSUMHASH' in param_dict:
            param_dict.pop ('CHECKSUMHASH')

        params_string=self.__get_param_string__ (param_dict ,False)
        return self.verify_checksum_by_str (params_string ,merchant_key ,checksum)


    def verify_checksum_by_str(self,param_str ,merchant_key ,checksum):
        IV="@@@@&&&&####$$$$"
        paytm_hash=self.__decode__ (checksum ,IV ,merchant_key)
        salt=paytm_hash [-4:]
        calculated_checksum=self.generate_checksum_by_str (param_str ,merchant_key ,salt=salt)
        return calculated_checksum == checksum

class PaymentTransactionAtom(models.Model):
    _inherit = 'payment.transaction'

    paytm_txn_type = fields.Char('Transaction type')

    @api.model
    def _paytm_form_get_tx_from_data(self ,data):
        reference =data.get ('ORDERID')
        if not reference:
            error_msg=_ ('Paytm: received data with missing reference (%s)') % (reference)
            _logger.info (error_msg)
            raise ValidationError (error_msg)

        txs=self.env ['payment.transaction'].search ([('reference' ,'=' ,reference)])
        if not txs or len (txs) > 1:
            error_msg='Paytm: received data for reference %s' % (reference)
            if not txs:
                error_msg+='; no order found'
            else:
                error_msg+='; multiple order found'
            _logger.info (error_msg)
            raise ValidationError (error_msg)
        return txs [0]


    def _paytm_form_get_invalid_parameters(self ,data):
        invalid_parameters=[]
        if self.acquirer_reference and data.get ('mmp_txn') != self.acquirer_reference:
            invalid_parameters.append (('ORDERID' ,data.get ('ORDERID') ,self.acquirer_reference))

        return invalid_parameters


    def _paytm_form_validate(self ,data):
        status=data.get ('STATUS')
        result=self.write ({
            'acquirer_reference':self.env ['payment.acquirer'].search ([]) ,
            'date':fields.Datetime.now () ,

        })
        if status == 'TXN_SUCCESS':
            self._set_transaction_done ()
        elif status != 'TXN_FAILED':
            self._set_transaction_cancel ()
        else:
            self._set_transaction_pending ()
        return result