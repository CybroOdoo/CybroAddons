# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Prasudhi A (odoo@cybrosys.com)
#
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
################################################################################
from odoo.tests import common
from odoo import Command

class TestPurchaseOrderlineImage(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create a test product with an image
        # Using a minimal base64 valid image string for testing
        cls.test_image_base64 = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
        
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product with Image',
            'type': 'consu',
            'image_128': cls.test_image_base64,
        })
        
        # Use an existing partner to avoid NotNullViolation from other modules
        cls.partner = cls.env.user.partner_id
        
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                Command.create({
                    'product_id': cls.product.id,
                    'product_qty': 1.0,
                    'price_unit': 100.0,
                })
            ]
        })

    def test_01_order_line_image(self):
        """Test if the purchase order line image matches the product image"""
        order_line = self.purchase_order.order_line[0]
        self.assertEqual(
            order_line.order_line_image,
            self.product.image_128,
            "Purchase order line image should match the product image."
        )

    def test_02_show_product_image_setting(self):
        """Test the computation of show_product_image_setting"""
        
        ResConfigSettings = self.env['res.config.settings']
        
        # Enable the setting via config settings
        settings = ResConfigSettings.create({
            'show_product_image_in_report_purchase': True
        })
        settings.execute()
        
        # Invalidate cache to force recomputation
        self.purchase_order.invalidate_recordset(['show_product_image_setting'])
        
        self.assertTrue(
            self.purchase_order.show_product_image_setting,
            "Setting should be True when parameter is enabled"
        )
        
        # Disable the setting via config settings
        settings = ResConfigSettings.create({
            'show_product_image_in_report_purchase': False
        })
        settings.execute()
        
        # Invalidate cache to force recomputation
        self.purchase_order.invalidate_recordset(['show_product_image_setting'])
        
        self.assertFalse(
            self.purchase_order.show_product_image_setting,
            "Setting should be False when parameter is disabled"
        )

    def test_03_res_config_settings(self):
        """Test if the res.config.settings properly sets the config parameter"""
        
        ResConfigSettings = self.env['res.config.settings']
        
        # Create settings with the boolean field checked
        settings = ResConfigSettings.create({
            'show_product_image_in_report_purchase': True
        })
        settings.execute()
        
        param_value = self.env['ir.config_parameter'].sudo().get_param(
            'purchase_orderline_image.show_product_image_in_report_purchase'
        )
        self.assertEqual(param_value, 'True', "Config parameter should be 'True'")
        
        # Create settings with the boolean field unchecked
        settings = ResConfigSettings.create({
            'show_product_image_in_report_purchase': False
        })
        settings.execute()
        
        param_value = self.env['ir.config_parameter'].sudo().get_param(
            'purchase_orderline_image.show_product_image_in_report_purchase'
        )
        # When unchecked, Odoo may delete the parameter causing get_param to return False
        self.assertIn(param_value, [False, 'False', ''], "Config parameter should be evaluated to False")
