# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys(<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
import json

class TestWebsiteProductCustomizer(TransactionCase):

    @classmethod
    def setUpClass(cls):
        """Setup Class for Website Product Customizer"""
        super(TestWebsiteProductCustomizer, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        cls.category = cls.env['product.public.category'].create({
            'name': 'Designable Category'
        })
        
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Custom T-Shirt',
            'is_designable': True,
            'design_category_id': cls.category.id,
            'list_price': 20.0,
        })
        cls.product = cls.product_tmpl.product_variant_ids[0]

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

    def test_01_product_template_compute(self):
        """Test product template compute fields related to templates."""
        template = self.env['product.design.template'].create({
            'name': 'Basic Design',
            'product_tmpl_id': self.product_tmpl.id,
            'design_data': '{}',
            'active': True,
        })
        self.product_tmpl.invalidate_model(['design_template_count'])
        self.assertEqual(self.product_tmpl.design_template_count, 1)

    def test_02_design_customization_creation(self):
        """Test customization creation sequence and states."""
        customization = self.env['product.design.customization'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'partner_id': self.partner.id,
            'design_json': json.dumps({'objects': [{'type': 'i-text', 'text': 'Hello'}]})
        })
        self.assertTrue(customization.name != 'New')
        self.assertEqual(customization.state, 'draft')

    def test_03_sale_order_computes(self):
        """Test sale order has_design_products and count computes."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        
        customization = self.env['product.design.customization'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'partner_id': self.partner.id,
        })

        line1 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'design_customization_id': customization.id,
        })

        order.invalidate_model(['has_design_products', 'design_customization_count'])
        
        self.assertTrue(order.has_design_products)
        self.assertEqual(order.design_customization_count, 1)
        self.assertTrue(line1.is_designed)

    def test_04_cart_find_product_line(self):
        """Test that force_new_design_line excludes lines with customizations."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        
        customization = self.env['product.design.customization'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'partner_id': self.partner.id,
        })

        # Line with customization
        line1 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'design_customization_id': customization.id,
        })
        
        # When finding a line with force_new_design_line=True, it should NOT return line1
        candidates = order._cart_find_product_line(self.product.id, self.product.uom_id.id, force_new_design_line=True)
        self.assertNotIn(line1.id, candidates.ids)
