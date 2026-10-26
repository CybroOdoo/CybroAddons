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
"""Tests for the sales performance wizard."""
from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import PerformanceCommon


@tagged('post_install', '-at_install')
class TestSalesPerformance(PerformanceCommon):
    """Figures and validations of the sales performance report."""

    def test_manager_figures(self):
        """Totals per salesperson are computed from their orders."""
        lines = self._sales_lines(self.admin, self.alice | self.bob)
        by_user = {line.user_id: line for line in lines}
        alice, bob = by_user[self.alice], by_user[self.bob]
        self.assertEqual(alice.estimated_revenue, 20.0)
        self.assertEqual(alice.total_sale_order, 1)
        self.assertEqual(alice.sale_order_done, 1)
        self.assertEqual(alice.avg_price, 20.0)
        self.assertEqual(bob.net_revenue, 30.0)
        self.assertAlmostEqual(bob.overall_performance, 50.0)

    def test_quotations_and_cancelled_orders(self):
        """Estimated revenue includes quotations, never cancelled orders."""
        self._make_order(self.alice, qty=1, confirm=False)
        cancelled = self._make_order(self.alice, qty=5)
        cancelled._action_cancel()
        line = self._sales_lines(self.admin, self.alice)
        self.assertEqual(line.total_sale_order, 2)
        self.assertEqual(line.sale_order_done, 1)
        self.assertEqual(line.estimated_revenue, 30.0)
        self.assertEqual(line.net_revenue, 20.0)

    def test_user_without_order(self):
        """A sales person without orders still has an empty row."""
        carol = self.env['res.users'].create({
            'name': 'Carol', 'login': 'perf_carol',
            'group_ids': [Command.link(
                self.env.ref('sales_team.group_sale_salesman').id)]})
        line = self._sales_lines(self.admin, carol)
        self.assertEqual(line.total_sale_order, 0)
        self.assertEqual(line.avg_price, 0.0)

    def test_team_filter_and_separated_orders(self):
        """Orders handled for another team are reported as separated."""
        team = self.env['crm.team'].create({
            'name': 'Perf Team', 'member_ids': [Command.set(self.alice.ids)]})
        other = self.env['crm.team'].create({'name': 'Other Team'})
        self._make_order(self.alice, qty=1, team_id=team.id)
        self._make_order(self.alice, qty=1, team_id=other.id)
        lines = self._sales_lines(
            self.admin, sales_team_ids=[Command.set(team.ids)])
        self.assertEqual(lines.user_id, self.alice)
        self.assertEqual(lines.team_id, team)
        self.assertEqual(lines.total_sale_order, 3)
        # Two of the four orders of the period have another team than hers.
        self.assertAlmostEqual(lines.overall_performance_separate, 50.0)

    def test_default_scope_lists_internal_users(self):
        """Without selection every internal user of the company is listed."""
        lines = self._sales_lines(self.admin)
        self.assertIn(self.alice, lines.user_id)
        self.assertIn(self.bob, lines.user_id)
        self.assertNotIn(
            self.env.ref('base.public_user'), lines.user_id)

    def test_end_date_is_inclusive(self):
        """An order placed late on the end date is part of the report."""
        self._make_order(self.alice, qty=1, date_order='2020-06-30 23:30:00')
        line = self._sales_lines(
            self.admin, self.alice, up_to_date_report=False,
            start_date='2020-06-30', end_date='2020-06-30')
        self.assertEqual(line.total_sale_order, 1)

    def test_returned_orders(self):
        """An order with an incoming picking counts once as returned."""
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'incoming'),
             ('company_id', '=', self.env.company.id)], limit=1)
        for _ in range(2):
            self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'sale_id': self.alice_order.id,
            })
        line = self._sales_lines(self.admin, self.alice)
        self.assertEqual(line.returned_orders, 1)

    def test_drill_down(self):
        """The line button opens exactly the orders that were counted."""
        line = self._sales_lines(self.admin, self.alice)
        action = line.action_sale_order()
        self.assertEqual(action['res_model'], 'sale.order')
        self.assertEqual(
            action['domain'], [('id', 'in', self.alice_order.ids)])

    def test_drill_down_without_orders(self):
        """A sales person without orders raises a clear error."""
        carol = self.env['res.users'].create({
            'name': 'Carol', 'login': 'perf_carol',
            'group_ids': [Command.link(
                self.env.ref('sales_team.group_sale_salesman').id)]})
        line = self._sales_lines(self.admin, carol)
        with self.assertRaises(UserError):
            line.action_sale_order()

    def test_no_sales_person_found(self):
        """A team without member raises a clear error."""
        team = self.env['crm.team'].create({'name': 'Empty Team'})
        wizard = self.env['sales.performance'].create(
            {'sales_team_ids': [Command.set(team.ids)]})
        with self.assertRaises(UserError):
            wizard.action_sales_performance()

    def test_end_before_start_is_rejected(self):
        """Wizard refuses an inverted date range."""
        with self.assertRaises(ValidationError):
            self.env['sales.performance'].create({
                'start_date': '2026-02-01', 'end_date': '2026-01-01'})
