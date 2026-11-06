# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.addons.payment.tests.common import PaymentCommon


class PaytabsCommon(PaymentCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.profile_id = '12345'
        cls.api_key = 'dummy_server_key'
        cls.api_url = 'https://secure.paytabs.com/payment/request'

        cls.paytabs = cls._prepare_provider('paytabs', update_values={
            'profile_key': cls.profile_id,
            'api_key': cls.api_key,
            'domain': cls.api_url,
        })
        cls.provider = cls.paytabs

        cls.payment_method_paytabs = cls.env.ref(
            'payment_paytabs_odoo.payment_method_paytabs', raise_if_not_found=False
        )
        if cls.payment_method_paytabs:
            cls.payment_method_paytabs.active = True
            cls.payment_method = cls.payment_method_paytabs
            cls.payment_method_id = cls.payment_method.id

        cls.reference = 'tx_paytabs_test_123'
        cls.tran_ref = 'TST2600100000000'
        cls.redirect_url = 'https://secure.paytabs.com/payment/page/503B8D97'

        cls.redirect_response = {
            'tran_ref': cls.tran_ref,
            'tran_type': 'Sale',
            'cart_id': cls.reference,
            'cart_description': cls.reference,
            'cart_currency': cls.currency.name,
            'cart_amount': str(cls.amount),
            'customer_details': {'name': cls.partner.name, 'email': cls.partner.email},
            'redirect_url': cls.redirect_url,
        }

        cls.return_data_authorized = {
            'cartId': cls.reference,
            'tranRef': cls.tran_ref,
            'respCode': 'G12345',
            'respStatus': 'A',
            'respMessage': 'Authorised',
        }

        cls.return_data_pending = {
            'cartId': cls.reference,
            'tranRef': cls.tran_ref,
            'respCode': 'G12346',
            'respStatus': 'H',
            'respMessage': 'Hold',
        }

        cls.return_data_canceled = {
            'cartId': cls.reference,
            'tranRef': cls.tran_ref,
            'respCode': 'G12347',
            'respStatus': 'C',
            'respMessage': 'Cancelled',
        }

        cls.webhook_data_authorized = {
            'tran_ref': cls.tran_ref,
            'tran_type': 'Sale',
            'cart_id': cls.reference,
            'cart_amount': cls.amount,
            'cart_currency': cls.currency.name,
            'payment_result': {
                'response_status': 'A',
                'response_code': '100',
                'response_message': 'Authorised',
            },
        }

        cls.webhook_data_declined = {
            'tran_ref': cls.tran_ref,
            'tran_type': 'Sale',
            'cart_id': cls.reference,
            'cart_amount': cls.amount,
            'cart_currency': cls.currency.name,
            'payment_result': {
                'response_status': 'D',
                'response_code': '200',
                'response_message': 'Declined',
            },
        }

