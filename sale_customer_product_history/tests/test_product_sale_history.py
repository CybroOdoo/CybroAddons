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


class TestProductSaleHistory(TransactionCase):
    """Tests for customer and product filtering in sale history."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({'name': 'History Customer'})
        cls.other_customer = cls.env['res.partner'].create(
            {'name': 'Other History Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'History Product',
            'list_price': 30.0,
        })
        cls.other_product = cls.env['product.product'].create({
            'name': 'Other History Product',
            'list_price': 50.0,
        })

    def _create_order(self, partner, product, quantity, price, confirm=False):
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': quantity,
                'price_unit': price,
            })],
        })
        if confirm:
            order.action_confirm()
        return order

    def test_history_contains_only_confirmed_matching_customer_product(self):
        matching_order = self._create_order(
            self.customer, self.product, 2, 25.0, confirm=True)
        self._create_order(self.customer, self.product, 4, 20.0)
        self._create_order(
            self.customer, self.other_product, 1, 50.0, confirm=True)
        self._create_order(
            self.other_customer, self.product, 3, 30.0, confirm=True)
        source_order = self._create_order(self.customer, self.product, 1, 30.0)

        action = source_order.order_line.get_product_history_data()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'product.sale.order.history')
        self.assertEqual(action['target'], 'new')
        history = self.env['product.sale.order.history'].browse(action['res_id'])
        self.assertEqual(history.product_id, self.product)
        self.assertEqual(len(history.product_sale_history_ids), 1)
        history_line = history.product_sale_history_ids
        self.assertEqual(history_line.sale_order_id, matching_order)
        self.assertEqual(float(history_line.history_price), 25.0)
        self.assertEqual(history_line.history_qty, 2.0)
        self.assertEqual(history_line.history_total, matching_order.amount_total)

    def test_history_is_empty_when_customer_has_no_confirmed_product_sales(self):
        draft_order = self._create_order(
            self.customer, self.product, 1, 30.0)

        action = draft_order.order_line.get_product_history_data()
        history = self.env['product.sale.order.history'].browse(action['res_id'])

        self.assertEqual(history.product_id, self.product)
        self.assertFalse(history.product_sale_history_ids)
