# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.addons.payment_payplug_acquirer.controllers.payment_payplug_acquirer import PaymentPayPlug

class TestPaymentPayPlugAcquirer(TransactionCase):
    """
    Test suite for controllers/payment_payplug_acquirer.py
    """

    def setUp(self):
        super(TestPaymentPayPlugAcquirer, self).setUp()
        self.controller = PaymentPayPlug()
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
        self.payment_method = self.env.ref('payment_payplug_acquirer.payment_method_payplug')
        self.transaction = self.env['payment.transaction'].create({
            'amount': 100.0,
            'currency_id': self.env.company.currency_id.id,
            'provider_id': self.payment_provider.id,
            'payment_method_id': self.payment_method.id,
            'reference': 'TEST-REF-123',
            'partner_id': self.env.user.partner_id.id,
            'provider_reference': 'payplug_test_ref',
        })

    @patch('odoo.addons.payment_payplug_acquirer.controllers.payment_payplug_acquirer.payplug.Payment.retrieve')
    def test_payplug_return(self, mock_payplug_retrieve):
        """Test payplug_return controller method."""
        class FakeRequest:
            def __init__(self, env):
                self.env = env
                self.redirect = MagicMock(return_value='redirected')

        fake_request = FakeRequest(self.env)

        mock_payment_payplug = MagicMock()
        mock_payment_payplug.id = 'payplug_test_ref'
        mock_payment_payplug.is_paid = True
        mock_payment_payplug.failure = None
        mock_payplug_retrieve.return_value = mock_payment_payplug

        controller_module = __import__(
            'odoo.addons.payment_payplug_acquirer.controllers.payment_payplug_acquirer',
            fromlist=['request']
        )

        post_data = {
            'transaction': str(self.transaction.id),
        }
        
        with patch.object(controller_module, 'request', fake_request), patch(
            'odoo.addons.payment.models.payment_transaction.PaymentTransaction._handle_notification_data'
        ) as mock_handle:
            res = self.controller.payplug_return(**post_data)
            
            mock_payplug_retrieve.assert_called_once_with('payplug_test_ref')
            mock_handle.assert_called_once_with('payplug', mock_payment_payplug)
            fake_request.redirect.assert_called_once_with('/payment/status')
