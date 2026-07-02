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
from odoo.exceptions import UserError

class TestProductProduct(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestProductProduct, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Setup configuration parameters
        cls.env['ir.config_parameter'].sudo().set_param('customer_product_qr.config.product_prefix', 'PROD-')
        
        # Create a product category
        cls.category = cls.env['product.category'].create({'name': 'Test Category'})

    def test_01_product_create_sequence(self):
        """Test sequence and QR generation on product creation"""
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'categ_id': self.category.id,
        })
        self.assertTrue(product.sequence)
        self.assertTrue(product.sequence.startswith('PROD-'))
        self.assertTrue(product.qr)

    def test_02_product_create_without_prefix(self):
        """Test error when creating product without prefix"""
        self.env['ir.config_parameter'].sudo().set_param('customer_product_qr.config.product_prefix', False)
        with self.assertRaises(UserError):
            self.env['product.product'].create({
                'name': 'Test Product No Prefix',
                'categ_id': self.category.id,
            })
        # Revert
        self.env['ir.config_parameter'].sudo().set_param('customer_product_qr.config.product_prefix', 'PROD-')

    def test_03_product_action_generate_sequence(self):
        """Test manual generation of sequence for product"""
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'categ_id': self.category.id,
        })
        product.sequence = False
        product.action_generate_sequence()
        self.assertTrue(product.sequence)
        self.assertTrue(product.sequence.startswith('PROD-'))

    def test_04_product_action_generate_qr(self):
        """Test QR code generation for product"""
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'categ_id': self.category.id,
        })
        product.qr = False
        action = product.action_generate_qr()
        self.assertTrue(product.qr)
        self.assertEqual(action.get('type'), 'ir.actions.report')

    def test_05_product_get_product_by_qr(self):
        """Test fetching product by QR sequence"""
        product = self.env['product.product'].create({
            'name': 'Test Product QR',
            'categ_id': self.category.id,
        })
        product.sequence = str(product.id)
        fetched_id = product.get_product_by_qr()
        self.assertEqual(fetched_id, product.id)
