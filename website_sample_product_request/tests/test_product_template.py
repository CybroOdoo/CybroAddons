# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Shikhil (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, Form

from odoo.tests import Form



class TestProductTemplateAndSaleOrder(TransactionCase):

    def setUp(self):
        super().setUp()


        # Create a test customer
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
        })

        # Create a non-sample product
        self.regular_product = self.env['product.product'].create({
            'name': 'Regular Product',
            'list_price': 100.0,
        })

        # Create a sample product template / product
        self.sample_product = self.env['product.product'].create({
            'name': 'Sample Product',
            'list_price': 50.0,
            'is_sample_product': True,
        })


    def test_is_sample_product_price_onchange(self):
        """
        Test that list_price changes to 0.0
        when is_sample_product is set to True using Form.
        """


        product_form = Form(self.env['product.template'])
        product_form.name = 'Test Onchange Product'
        product_form.list_price = 120.0

        # When is_sample_product is false, price remains unchanged
        self.assertEqual(product_form.list_price, 120.0)


        # Set is_sample_product to True
        product_form.is_sample_product = True

        # Price should be reset to 0.0 by the onchange method
        self.assertEqual(product_form.list_price, 0.0)


        # Create the product and check values
        product = product_form.save()

        self.assertTrue(product.is_sample_product)
        self.assertEqual(product.list_price, 0.0)


    def test_onchange_method_direct_call(self):
        """Directly test the python onchange method logic."""


        template = self.env['product.template'].create({
            'name': 'Direct Test Product',
            'list_price': 80.0,
            'is_sample_product': True,
        })

        template._onchange_is_sample_product()

        self.assertEqual(template.list_price, 0.0)


        template.is_sample_product = False
        template.list_price = 80.0

        template._onchange_is_sample_product()

        self.assertEqual(template.list_price, 80.0)


    def test_sale_order_sample_flag(self):
        """Test creating a sale order and setting the is_sample_order field."""


        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'is_sample_order': True,
        })

        self.assertTrue(sale_order.is_sample_order)


        # Create order line
        self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.sample_product.id,
            'product_uom_qty': 1,
        })

        self.assertEqual(len(sale_order.order_line), 1)

        self.assertTrue(
            sale_order.order_line[0].product_template_id.is_sample_product
        )
