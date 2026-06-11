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

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPaymentProvider(TransactionCase):
    """Test PaymentProvider model functions from models/payment_provider.py"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        providers = cls.env['payment.provider'].search([('code', '=', 'myfatoorah')])
        if len(providers) > 1:
            providers[1:].unlink()
        
        cls.provider = providers[0] if providers else cls.env['payment.provider'].create({
            'name': 'Test MyFatoorah',
            'code': 'myfatoorah',
            'state': 'test',
            'myfatoorah_token': 'fake_token_123',
        })
        cls.provider.write({
            'state': 'test',
            'myfatoorah_token': 'fake_token_123',
        })



    def test_myfatoorah_get_api_url_test(self):
        """Test API URL for test state."""
        self.provider.state = 'test'
        url = self.provider._myfatoorah_get_api_url()
        self.assertEqual(url, 'https://apitest.myfatoorah.com/')

    def test_myfatoorah_get_api_url_prod(self):
        """Test API URL for enabled state."""
        self.provider.state = 'enabled'
        url = self.provider._myfatoorah_get_api_url()
        self.assertEqual(url, 'https://api.myfatoorah.com/')
