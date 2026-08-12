# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################

from odoo.addons.payment.tests.common import PaymentCommon


class BitPayCommon(PaymentCommon):
    """Common Setup Class for BitPay Gateway Tests."""

    @classmethod
    def setUpClass(cls):
        """Set Up Class Method for BitPay Tests."""
        super().setUpClass()
        cls.provider = cls._prepare_provider('bitpay', update_values={
            'bitpay_pos_token': 'DummyPOSBitPayToken1234567890',
            'state': 'test',
        })
        cls.notification_data = {
            'event': {'name': 'invoice_completed'},
            'data': {
                'id': 'InvoiceBitPay123',
                'orderId': cls.reference,
                'price': cls.amount,
                'currency': cls.currency.name,
                'status': 'complete',
            },
        }
