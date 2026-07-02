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

from odoo.tests.common import TransactionCase

class TestResConfigSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestResConfigSettings, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Setup configuration parameters
        cls.env['ir.config_parameter'].sudo().set_param('customer_product_qr.config.customer_prefix', 'CUST-')
        cls.env['ir.config_parameter'].sudo().set_param('customer_product_qr.config.product_prefix', 'PROD-')

    def test_01_res_config_settings(self):
        """Test getting and setting of QR prefixes in res.config.settings"""
        settings = self.env['res.config.settings'].create({
            'customer_prefix': 'TEST-CUST-',
            'product_prefix': 'TEST-PROD-',
        })
        settings.set_values()
        
        customer_prefix = self.env['ir.config_parameter'].sudo().get_param('customer_product_qr.config.customer_prefix')
        product_prefix = self.env['ir.config_parameter'].sudo().get_param('customer_product_qr.config.product_prefix')
        
        self.assertEqual(customer_prefix, 'TEST-CUST-')
        self.assertEqual(product_prefix, 'TEST-PROD-')
        
        # Test get_values
        res = settings.get_values()
        self.assertEqual(res.get('customer_prefix'), 'TEST-CUST-')
        self.assertEqual(res.get('product_prefix'), 'TEST-PROD-')
        
        # Revert to original setup values for other tests
        self.env['ir.config_parameter'].sudo().set_param('customer_product_qr.config.customer_prefix', 'CUST-')
        self.env['ir.config_parameter'].sudo().set_param('customer_product_qr.config.product_prefix', 'PROD-')
