# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestPaymentTransaction(TransactionCase):
    """
    Test suite for models/payment_transaction.py
    """

    def setUp(self):
        super(TestPaymentTransaction, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'zip': '12345',
            'email': 'test@example.com',
            'city': 'Test City',
            'country_id': self.env.ref('base.fr').id,
        })
        self.payment_provider = self.env['payment.provider'].search([('code', '=', 'payplug')], limit=1)
        if not self.payment_provider:
            self.payment_provider = self.env['payment.provider'].create({
                'name': 'PayPlug',
                'code': 'payplug',
                'state': 'test',
                'payplug_end_point': 'https://api.payplug.com/v1/payments',
                'payplug_secret_key': 'test_secret_key',
            })
        else:
            self.payment_provider.write({
                'payplug_end_point': 'https://api.payplug.com/v1/payments',
                'payplug_secret_key': 'test_secret_key',
            })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'name': 'Test Product',
                    'product_id': self.env['product.product'].create({'name': 'Test'}).id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                })
            ]
        })
        self.payment_method = self.env.ref('payment_payplug_acquirer.payment_method_payplug')
        self.transaction = self.env['payment.transaction'].create({
            'amount': 100.0,
            'currency_id': self.env.company.currency_id.id,
            'provider_id': self.payment_provider.id,
            'payment_method_id': self.payment_method.id,
            'reference': 'TEST-REF-123',
            'partner_id': self.partner.id,
            'sale_order_ids': [(6, 0, self.sale_order.ids)],
        })

    def test_compute_reference(self):
        """Test reference computation prefix singularization for payplug."""
        ref = self.env['payment.transaction']._compute_reference('payplug', prefix='SO/123')
        self.assertIn('tx', ref)

    @patch('odoo.addons.payment_payplug_acquirer.models.payment_provider.PaymentProvider._payplug_make_request')
    def test_get_specific_rendering_values(self, mock_make_request):
        """Test generating rendering values and digital signature generation."""
        import odoo.addons.payment_payplug_acquirer.models.payment_transaction as pt_mod
        original_request = pt_mod.request
        mock_request = MagicMock()
        mock_request.env = self.env
        pt_mod.request = mock_request
        
        try:
            mock_make_request.return_value = {
                'id': 'payplug_response_id',
                'hosted_payment': {'payment_url': 'https://payplug.com/pay'},
            }
            
            processing_values = {
                'reference': 'TEST-REF-123',
                'amount': 100.0,
            }
            
            res = self.transaction._get_specific_rendering_values(processing_values)
            
            self.assertEqual(self.transaction.provider_reference, 'payplug_response_id')
            self.assertEqual(res.get('api_url'), 'https://payplug.com/pay')
            mock_make_request.assert_called_once()
            
            called_args, called_kwargs = mock_make_request.call_args
            self.assertEqual(called_args[0], 'https://api.payplug.com/v1/payments')
            self.assertIn('customer', called_args[1])
            self.assertIn('hosted_payment', called_args[1])
            self.assertIn('metadata', called_args[1])
            self.assertIn('DigitalKey', called_args[1]['metadata'])
        finally:
            pt_mod.request = original_request

    def test_get_tx_from_notification_data(self):
        """Test retrieving transaction from notification data and verifying signature."""
        self.transaction.provider_reference = 'payplug_response_id'
        
        class MockNotificationData:
            def __init__(self, tx_id, key):
                self._attributes = {'id': tx_id}
                self.metadata = {'DigitalKey': key}
                
        vals = {
            'reference': self.transaction.reference.split('-')[0],
            'customer_name': self.transaction.partner_id.name,
            'customer_postcode': self.transaction.partner_id.zip,
        }
        expected_key = self.payment_provider._playplug_generate_digital_sign(vals)
        
        mock_data = MockNotificationData('payplug_response_id', expected_key)
        
        tx = self.env['payment.transaction']._get_tx_from_notification_data('payplug', mock_data)
        self.assertEqual(tx, self.transaction)

    def test_get_tx_from_notification_data_invalid_signature(self):
        """Test failure when signature validation fails."""
        self.transaction.provider_reference = 'payplug_response_id'
        
        class MockNotificationData:
            def __init__(self, tx_id):
                self._attributes = {'id': tx_id}
                self.metadata = {'DigitalKey': 'INVALID_SIGNATURE'}
                
        mock_data = MockNotificationData('payplug_response_id')
        
        with self.assertRaises(ValidationError) as e:
            self.env['payment.transaction']._get_tx_from_notification_data('payplug', mock_data)
        
        self.assertIn("Invalid Key", str(e.exception))

    def test_process_notification_data_paid(self):
        """Test transaction processing when paid successfully."""
        class MockNotificationData:
            is_paid = True
            failure = None
            
        mock_data = MockNotificationData()
        self.transaction._process_notification_data(mock_data)
        self.assertEqual(self.transaction.state, 'done')

    def test_process_notification_data_pending(self):
        """Test transaction processing when pending/error."""
        class MockNotificationData:
            is_paid = False
            failure = None
            
        mock_data = MockNotificationData()
        self.transaction._process_notification_data(mock_data)
        self.assertEqual(self.transaction.state, 'pending')

    def test_process_notification_data_failure(self):
        """Test transaction processing when failure occurs."""
        class MockNotificationData:
            is_paid = False
            failure = "Insufficient funds"
            
        mock_data = MockNotificationData()
        self.transaction._process_notification_data(mock_data)
        self.assertEqual(self.transaction.state, 'error')
