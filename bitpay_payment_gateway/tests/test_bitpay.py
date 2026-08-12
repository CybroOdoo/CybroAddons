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

import json
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.http_common import PaymentHttpCommon
from odoo.addons.bitpay_payment_gateway.controllers.bitpay_payment_gateway import BitPayController
from odoo.addons.bitpay_payment_gateway.tests.common import BitPayCommon


@tagged('post_install', '-at_install')
class BitPayTest(BitPayCommon, PaymentHttpCommon):
    """BitPay Payment Gateway Test Cases."""

    def test_rendering_values(self):
        """Test Generation of Specific Rendering Values for BitPay Form Redirect."""
        tx = self._create_transaction('redirect')

        with patch(
            'odoo.addons.bitpay_payment_gateway.models.payment_provider.PaymentProvider._bitpay_make_request',
            return_value={'id': 'InvoiceBitPay123', 'url': 'https://test.bitpay.com/invoice?id=InvoiceBitPay123'},
        ):
            rendering_values = tx._get_specific_rendering_values({})

        self.assertEqual(rendering_values['api_url'], 'https://test.bitpay.com/invoice')
        self.assertEqual(rendering_values['invoice_id'], 'InvoiceBitPay123')
        self.assertEqual(tx.provider_reference, 'InvoiceBitPay123')

    def test_extract_reference(self):
        """Test Extraction of Transaction Reference from BitPay Payload."""
        ref = self.env['payment.transaction']._extract_reference('bitpay', self.notification_data)
        self.assertEqual(ref, self.reference)

    def test_extract_amount_data(self):
        """Test Extraction of Amount and Currency Code from BitPay Payload."""
        tx = self._create_transaction('redirect')
        amount_data = tx._extract_amount_data(self.notification_data)
        self.assertEqual(amount_data['amount'], self.amount)
        self.assertEqual(amount_data['currency_code'], self.currency.name)

    @mute_logger(
        'odoo.addons.bitpay_payment_gateway.controllers.main',
        'odoo.addons.bitpay_payment_gateway.models.payment_transaction',
    )
    def test_webhook_signature_and_processing(self):
        """Test Processing of Webhook Payload from BitPay Controller."""
        tx = self._create_transaction('redirect')
        payload = {
            'event': {'name': 'invoice_completed'},
            'data': {
                'id': 'InvoiceBitPay123',
                'orderId': tx.reference,
                'price': tx.amount,
                'currency': tx.currency_id.name,
                'status': 'complete',
            },
        }
        tx._process_notification_data(payload['data'])
        self.assertEqual(tx.state, 'done')

    def test_all_bitpay_status_mappings(self):
        """Test Status Mapping Rules for All BitPay Invoice Statuses."""
        status_mappings = [
            ('new', 'pending'),
            ('paid', 'done'),
            ('confirmed', 'done'),
            ('complete', 'done'),
            ('expired', 'cancel'),
            ('invalid', 'cancel'),
        ]
        for bitpay_status, expected_state in status_mappings:
            tx = self._create_transaction('redirect', reference=f'TEST_TX_{bitpay_status.upper()}')
            payload = {
                'id': f'INV_{bitpay_status}',
                'orderId': tx.reference,
                'price': tx.amount,
                'currency': tx.currency_id.name,
                'status': bitpay_status,
            }
            tx._process_notification_data(payload)
            self.assertEqual(tx.state, expected_state, f"Failed state mapping for status '{bitpay_status}'")
