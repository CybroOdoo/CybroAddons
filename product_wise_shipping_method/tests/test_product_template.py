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

from odoo.tests import tagged

from .common import ProductWiseShippingCommon


@tagged('post_install', '-at_install')
class TestProductTemplate(ProductWiseShippingCommon):

    def test_field_definition(self):
        field = self.env['product.template']._fields['shipping_method_id']
        self.assertEqual(field.type, 'many2one')
        self.assertEqual(field.comodel_name, 'delivery.carrier')
        self.assertEqual(field.string, 'Shipping Method')

    def test_default_is_empty(self):
        self.assertFalse(self.product_plain.shipping_method_id)

    def test_set_and_read_shipping_method(self):
        self.assertEqual(self.product_a1.shipping_method_id, self.carrier_a)
        self.assertEqual(self.product_b1.shipping_method_id, self.carrier_b)

    def test_change_and_clear_shipping_method(self):
        self.product_plain.shipping_method_id = self.carrier_b
        self.assertEqual(self.product_plain.shipping_method_id, self.carrier_b)
        self.product_plain.shipping_method_id = False
        self.assertFalse(self.product_plain.shipping_method_id)

    def test_variant_uses_template_shipping_method(self):
        variant = self.product_a1.product_variant_id
        self.assertEqual(
            variant.product_tmpl_id.shipping_method_id, self.carrier_a)

    def test_order_line_is_duplicated_field(self):
        field = self.env['sale.order.line']._fields['is_duplicated']
        self.assertEqual(field.type, 'boolean')
        self.assertFalse(field.default(self.env['sale.order.line']))
        self.assertFalse(field.copy)
