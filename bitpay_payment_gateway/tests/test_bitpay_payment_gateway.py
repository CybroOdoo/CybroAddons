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
from odoo.tests import tagged, HttpCase
from odoo.addons.bitpay_payment_gateway.tests.common import BitPayCommon


@tagged('post_install', '-at_install', 'bitpay_payment_gateway')
class TestBitPayPaymentGatewayController(HttpCase, BitPayCommon):
    """Test Suite for Controller Endpoints in BitPay Payment Gateway."""

    def setUp(self):
        """Set Up Controller Test Records."""
        super().setUp()
        self.tx = self._create_transaction(
            flow='redirect',
            provider_id=self.provider.id,
            reference=self.reference,
            amount=self.amount,
            currency_id=self.currency.id,
            partner_id=self.partner.id,
        )

    @patch('odoo.addons.bitpay_payment_gateway.models.payment_transaction.PaymentTransaction._bitpay_sync_live_invoice_status')
    def test_bitpay_return_route(self, mock_sync):
        """Test Customer Return Route Redirection to Payment Status Page."""
        response = self.url_open(
            '/payment/bitpay/return',
            data={'orderId': self.tx.reference},
            allow_redirects=False
        )
        self.assertIn(response.status_code, (302, 303))
        self.assertTrue(response.headers['Location'].endswith('/payment/status'))

    def test_bitpay_notification_route(self):
        """Test Webhook Notification Endpoint Request Handling."""
        payload = json.dumps({
            'data': {
                'id': 'InvoiceBitPay123',
                'orderId': self.tx.reference,
                'status': 'paid',
            }
        })
        response = self.url_open(
            '/payment/bitpay/notification',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'OK')
        self.tx.invalidate_recordset(['state'])
        self.assertEqual(self.tx.state, 'done')
