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

from unittest.mock import patch
from odoo.tests import tagged
from odoo.addons.bitpay_payment_gateway.tests.common import BitPayCommon


@tagged('post_install', '-at_install', 'bitpay_payment_gateway')
class TestPaymentTransaction(BitPayCommon):
    """Test Suite for PaymentTransaction Model Methods in BitPay Payment Gateway."""

    def setUp(self):
        """Set Up Test Transaction Record."""
        super().setUp()
        self.tx = self._create_transaction(
            flow='redirect',
            provider_id=self.provider.id,
            reference=self.reference,
            amount=self.amount,
            currency_id=self.currency.id,
            partner_id=self.partner.id,
        )

    @patch('odoo.addons.bitpay_payment_gateway.models.payment_provider.PaymentProvider._bitpay_make_request')
    def test_get_specific_rendering_values(self, mock_make_request):
        """Test Creation of BitPay Invoice Payload with Auto-Redirect."""
        mock_make_request.return_value = {
            'id': 'InvoiceBitPay999',
            'url': 'https://test.bitpay.com/invoice?id=InvoiceBitPay999',
        }
        processing_values = {
            'reference': self.tx.reference,
            'amount': self.tx.amount,
            'currency': self.currency,
            'partner_id': self.partner,
        }
        res = self.tx._get_specific_rendering_values(processing_values)

        self.assertEqual(res['api_url'], 'https://test.bitpay.com/invoice')
        self.assertEqual(res['invoice_id'], 'InvoiceBitPay999')

        # Verify autoRedirect and closeURL in API payload
        payload_sent = mock_make_request.call_args[1]['payload']
        self.assertTrue(payload_sent.get('autoRedirect'))
        self.assertIn('/payment/bitpay/return', payload_sent.get('closeURL'))

    def test_get_tx_from_notification_data(self):
        """Test Finding Payment Transaction Record from Webhook Notification Data."""
        notification_data = {
            'data': {
                'id': 'InvoiceBitPay999',
                'orderId': self.tx.reference,
            }
        }
        tx = self.env['payment.transaction']._get_tx_from_notification_data('bitpay', notification_data)
        self.assertEqual(tx, self.tx)

    def test_process_notification_data_paid(self):
        """Test Status 'paid' Updates Transaction State to 'done'."""
        notification_data = {
            'data': {
                'id': 'InvoiceBitPay999',
                'orderId': self.tx.reference,
                'status': 'paid',
            }
        }
        self.tx._process('bitpay', notification_data)
        self.assertEqual(self.tx.state, 'done')

    def test_process_notification_data_confirmed(self):
        """Test Status 'confirmed' Updates Transaction State to 'done'."""
        notification_data = {
            'data': {
                'id': 'InvoiceBitPay999',
                'orderId': self.tx.reference,
                'status': 'confirmed',
            }
        }
        self.tx._process('bitpay', notification_data)
        self.assertEqual(self.tx.state, 'done')

    def test_process_notification_data_complete(self):
        """Test Status 'complete' Updates Transaction State to 'done'."""
        notification_data = {
            'data': {
                'id': 'InvoiceBitPay999',
                'orderId': self.tx.reference,
                'status': 'complete',
            }
        }
        self.tx._process('bitpay', notification_data)
        self.assertEqual(self.tx.state, 'done')

    def test_process_notification_data_expired(self):
        """Test Status 'expired' Updates Transaction State to 'cancel'."""
        notification_data = {
            'data': {
                'id': 'InvoiceBitPay999',
                'orderId': self.tx.reference,
                'status': 'expired',
            }
        }
        self.tx._process('bitpay', notification_data)
        self.assertEqual(self.tx.state, 'cancel')

    def test_process_notification_data_invalid(self):
        """Test Status 'invalid' Updates Transaction State to 'cancel'."""
        notification_data = {
            'data': {
                'id': 'InvoiceBitPay999',
                'orderId': self.tx.reference,
                'status': 'invalid',
            }
        }
        self.tx._process('bitpay', notification_data)
        self.assertEqual(self.tx.state, 'cancel')

    @patch('odoo.addons.bitpay_payment_gateway.models.payment_provider.PaymentProvider._bitpay_make_request')
    def test_bitpay_sync_live_invoice_status(self, mock_make_request):
        """Test Syncing Live BitPay Invoice Status via API Query."""
        self.tx.provider_reference = 'InvoiceBitPay999'
        mock_make_request.return_value = {
            'data': {
                'id': 'InvoiceBitPay999',
                'status': 'complete',
            }
        }
        self.tx._bitpay_sync_live_invoice_status()
        self.assertEqual(self.tx.state, 'done')
