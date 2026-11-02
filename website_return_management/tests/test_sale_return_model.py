# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abbas P (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.sale_stock.tests.common import TestSaleStockCommon


@tagged('post_install', '-at_install')
class TestSaleReturnModel(TestSaleStockCommon):
    """Backend behaviour of sale.return and the smart buttons around it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)

    def setUp(self):
        super().setUp()
        self.order = self._so_deliver(self.product, quantity=5,
                                      partner=self.partner)
        self.delivery = self.order.picking_ids
        self.sale_return = self.env['sale.return'].create({
            'product_id': self.product.id,
            'sale_order_id': self.order.id,
            'quantity': 2,
        })
        self.delivery.return_order_id = self.sale_return

    def test_partner_defaults_from_sale_order(self):
        self.assertEqual(self.sale_return.partner_id, self.order.partner_id)

    def test_quantity_must_be_positive(self):
        for qty in (0, -1):
            with self.subTest(qty=qty), self.assertRaises(ValidationError):
                self.sale_return.quantity = qty

    def test_available_products_and_deliveries(self):
        self.assertEqual(self.sale_return.available_picking_ids,
                         self.delivery)
        self.assertEqual(self.sale_return.available_product_ids,
                         self.product)
        undelivered = self._so_deliver(self.product, quantity=1,
                                       picking=False, partner=self.partner)
        undelivered.picking_ids.unlink()
        other = self.env['sale.return'].create({
            'product_id': self.product.id,
            'sale_order_id': undelivered.id,
            'quantity': 1,
        })
        self.assertFalse(other.available_picking_ids)
        self.assertEqual(other.available_product_ids, self.product)

    def test_returnable_qty_subtracts_open_returns(self):
        returnable = self.env['sale.return']._get_returnable_qty(
            self.order, self.product)
        self.assertEqual(returnable, 3)
        self.sale_return.return_cancel()
        returnable = self.env['sale.return']._get_returnable_qty(
            self.order, self.product)
        self.assertEqual(returnable, 5)

    def test_confirm_validate_marks_return_done(self):
        self.assertEqual(self.sale_return.delivery_count, 1)
        self.assertEqual(self.sale_return.picking_count, 0)
        self.sale_return.return_confirm()
        self.assertEqual(self.sale_return.picking_count, 1)
        return_picking = self.sale_return.return_picking_ids
        return_picking.action_assign()
        return_picking.move_ids.quantity = 2
        return_picking.move_ids.picked = True
        return_picking.button_validate()
        self.assertEqual(return_picking.state, 'done')
        self.assertEqual(self.sale_return.state, 'done')

    def test_confirm_without_delivery_raises(self):
        other_product = self.env['product.product'].create({
            'name': 'Never Delivered', 'is_storable': True})
        sale_return = self.env['sale.return'].create({
            'product_id': other_product.id,
            'sale_order_id': self.order.id,
            'quantity': 1,
        })
        with self.assertRaises(UserError):
            sale_return.return_confirm()

    def test_cancel_cancels_open_return_picking(self):
        self.sale_return.return_confirm()
        return_picking = self.sale_return.return_picking_ids
        self.sale_return.return_cancel()
        self.assertEqual(self.sale_return.state, 'cancel')
        self.assertEqual(return_picking.state, 'cancel')

    def test_picking_actions(self):
        action = self.sale_return.action_view_delivery()
        self.assertEqual(action['res_id'], self.delivery.id)
        self.sale_return.return_confirm()
        action = self.sale_return.action_view_picking()
        self.assertEqual(action['res_id'],
                         self.sale_return.return_picking_ids.id)
        second = self.delivery.copy()
        second.return_order_id = self.sale_return
        action = self.sale_return.action_view_delivery()
        self.assertEqual(action['domain'],
                         [('id', 'in', (self.delivery | second).ids)])
        self.assertFalse(action['context']['create'])

    def test_onchange_product_sets_received_qty(self):
        with Form(self.sale_return) as form:
            form.product_id = self.env['product.product']
            form.product_id = self.product
            self.assertEqual(form.received_qty, 5)

    def test_sale_order_smart_button(self):
        self.assertEqual(self.order.return_order_count, 1)
        action = self.order.action_open_returns()
        self.assertEqual(action['domain'],
                         [('sale_order_id', '=', self.order.id)])
        other = self._so_deliver(self.product, quantity=1, picking=False,
                                 partner=self.partner)
        self.assertEqual(other.return_order_count, 0)

    def test_partner_smart_button(self):
        company = self.env['res.partner'].create({
            'name': 'Return Company', 'is_company': True})
        self.partner.parent_id = company
        self.partner.invalidate_recordset(['return_order_count'])
        company.invalidate_recordset(['return_order_count'])
        self.assertEqual(self.partner.return_order_count, 1)
        self.assertEqual(company.return_order_count, 1)
        action = company.action_open_returns()
        self.assertEqual(
            self.env['sale.return'].search(action['domain']),
            self.sale_return)

    def test_report_renders(self):
        html, _ = self.env['ir.actions.report']._render_qweb_html(
            'website_return_management.report_sale_returns',
            self.sale_return.ids)
        self.assertIn(self.sale_return.name, html.decode())
        self.assertEqual(self.sale_return._get_report_base_filename(),
                         'Sale Return - %s' % self.sale_return.name)
        self.assertEqual(self.sale_return.access_url,
                         '/my/return_orders/%s' % self.sale_return.id)
