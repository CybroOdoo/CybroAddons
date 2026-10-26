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
class TestViews(TransactionCase):

    def test_product_template_view(self):
        view = self.env.ref(
            'product_wise_shipping_method.'
            'product_template_view_form_inherit_product_wise_shipping_method')
        self.assertEqual(view.model, 'product.template')
        self.assertEqual(
            view.inherit_id,
            self.env.ref('product.product_template_only_form_view'))
        self.assertIn('shipping_method_id', view.arch_db)

    def test_sale_order_view(self):
        view = self.env.ref('product_wise_shipping_method.'
            'sale_order_view_form_inherit_product_wise_shipping_method')
        self.assertEqual(view.model, 'sale.order')
        self.assertEqual(view.inherit_id, self.env.ref('sale.view_order_form'))
        self.assertIn('action_open_delivery_wizard', view.arch_db)
        self.assertIn('draft', view.arch_db)
