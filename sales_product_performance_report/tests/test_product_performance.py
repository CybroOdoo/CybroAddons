#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Tests for the product performance wizard."""
from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import PerformanceCommon


@tagged('post_install', '-at_install')
class TestProductPerformance(PerformanceCommon):
    """Figures and validations of the product performance report."""

    def test_manager_sees_all_orders(self):
        """A user without own-documents restriction gets the full totals."""
        line = self._product_lines(self.admin)
        self.assertEqual(line.revenue, 50.0)
        self.assertEqual(line.total_order, 2)
        self.assertEqual(line.ordered_quantities, 5.0)
        self.assertAlmostEqual(line.avg_ordered_qty, 2.5)
        self.assertAlmostEqual(line.avg_price, 10.0)

    def test_only_confirmed_orders_are_counted(self):
        """Quotations and cancelled orders are not sales."""
        self._make_order(self.alice, qty=7, confirm=False)
        cancelled = self._make_order(self.alice, qty=9)
        cancelled._action_cancel()
        line = self._product_lines(self.admin)
        self.assertEqual(line.revenue, 50.0)

    def test_date_filter(self):
        """Orders outside the date range are excluded."""
        self._make_order(self.alice, qty=7, date_order='2020-01-10 10:00:00')
        line = self._product_lines(
            self.admin, up_to_date_report=False,
            start_date='2020-01-01', end_date='2020-12-31')
        self.assertEqual(line.revenue, 70.0)

    def test_end_date_is_inclusive(self):
        """An order placed late on the end date is part of the report."""
        self._make_order(self.alice, qty=4, date_order='2020-06-30 23:30:00')
        line = self._product_lines(
            self.admin, up_to_date_report=False,
            start_date='2020-06-30', end_date='2020-06-30')
        self.assertEqual(line.revenue, 40.0)

    def test_end_before_start_is_rejected(self):
        """Wizard refuses an inverted date range."""
        with self.assertRaises(ValidationError):
            self.env['product.performance'].create({
                'start_date': '2026-02-01',
                'end_date': '2026-01-01',
            })

    def test_no_products(self):
        """Action raises when no product exists in category."""
        empty_categ = self.env['product.category'].create({'name': 'Empty'})
        wizard = self.env['product.performance'].create({
            'categ_id': empty_categ.id,
        })
        with self.assertRaises(UserError):
            wizard.action_product_performance()

    def test_category_selection_and_unsold_product(self):
        """Without product selection the whole category is reported."""
        unsold = self.env['product.template'].create({
            'name': 'Unsold', 'categ_id': self.categ.id})
        wizard = self.env['product.performance'].create({
            'categ_id': self.categ.id, 'up_to_date_report': True})
        action = wizard.action_product_performance()
        lines = self.env['product.performance.line'].search(action['domain'])
        self.assertEqual(
            lines.product_tmpl_id, self.product.product_tmpl_id | unsold)
        self.assertEqual(lines.filtered(
            lambda line: line.product_tmpl_id == unsold).revenue, 0.0)
        # Running the same wizard again replaces its lines.
        wizard.action_product_performance()
        self.assertEqual(len(wizard.line_ids), 2)

    def test_default_category(self):
        """The wizard proposes a root category."""
        wizard = self.env['product.performance'].create({})
        self.assertFalse(wizard.categ_id.parent_id)

    def test_drill_down(self):
        """The line button opens the orders behind the figures."""
        line = self._product_lines(self.admin)
        action = line.action_sale_order()
        self.assertEqual(action['res_model'], 'sale.order')
        self.assertCountEqual(
            action['domain'][0][2],
            (self.alice_order | self.bob_order).ids)

    def test_drill_down_without_visible_order(self):
        """A line whose orders are not visible raises a clear error."""
        line = self._product_lines(self.alice)
        self.alice_order.user_id = self.bob
        with self.assertRaises(UserError):
            line.with_user(self.alice).action_sale_order()

    def test_multi_currency_is_converted(self):
        """Amounts of other currencies are converted, not summed as is."""
        company = self.env.company
        other = self.env['res.currency'].with_context(
            active_test=False).search(
                [('id', '!=', company.currency_id.id)], limit=1)
        other.active = True
        self.env['res.currency.rate'].create({
            'currency_id': other.id,
            'company_id': company.id,
            'name': fields.Date.subtract(fields.Date.today(), days=1),
            'rate': 2.0 * company.currency_id.rate,
        })
        pricelist = self.env['product.pricelist'].create({
            'name': 'Other currency', 'currency_id': other.id})
        self._make_order(self.alice, qty=1, pricelist_id=pricelist.id)
        line = self._product_lines(self.admin)
        self.assertEqual(line.total_order, 3)
        self.assertAlmostEqual(line.revenue, 55.0, places=2)

    def test_returns_and_warehouse(self):
        """Delivered and returned quantities come from the stock moves."""
        stock_product = self.env['product.product'].create({
            'name': 'Stock Product', 'is_storable': True,
            'categ_id': self.categ.id, 'taxes_id': [Command.clear()],
        })
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1)
        self.env['stock.quant']._update_available_quantity(
            stock_product, warehouse.lot_stock_id, 20.0)
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.alice.id,
            'order_line': [Command.create({
                'product_id': stock_product.id, 'product_uom_qty': 5.0,
                'price_unit': 10.0})],
        })
        order.action_confirm()
        picking = order.picking_ids
        picking.move_ids.quantity = 5.0
        picking.move_ids.picked = True
        picking._action_done()
        return_picking = picking._create_return()
        return_picking.move_ids.quantity = 2.0
        return_picking.move_ids.picked = True
        return_picking._action_done()

        line = self._product_lines(
            self.admin,
            product_ids=[Command.set(stock_product.product_tmpl_id.ids)])
        # Odoo counts the delivered quantity net of the returns.
        self.assertEqual(line.delivered_quantities, 3.0)
        self.assertEqual(line.returned_quantities, 2.0)
        self.assertEqual(line.quantity, 17.0)
        self.assertEqual(line.warehouse_id, warehouse)
