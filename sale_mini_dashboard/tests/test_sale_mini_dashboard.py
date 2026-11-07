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

from odoo import Command
from odoo.tests import TransactionCase, tagged
from odoo.tools import format_amount


@tagged('post_install', '-at_install')
class TestSaleMiniDashboard(TransactionCase):
    """Tests for the values displayed by the sale mini dashboard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Dashboard Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Dashboard Product',
            'list_price': 100.0,
        })
        cls.other_user = cls.env['res.users'].create({
            'name': 'Dashboard Other User',
            'login': 'dashboard_other_user',
        })

    def _create_order(self, user, confirm=False, state=None):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': user.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 2,
                'price_unit': 100.0,
                'tax_ids': [Command.clear()],
            })],
        })
        if confirm:
            order.action_confirm()
        if state:
            order.state = state
        return order

    def _amount(self, states):
        orders = self.env['sale.order'].search([('state', 'in', states)])
        return format_amount(
            self.env, sum(orders.mapped('amount_total')),
            self.env.company.currency_id)

    def test_dashboard_counts(self):
        """Counts follow the order state and the salesperson."""
        before = self.env['sale.order'].get_dashboard_values()
        user = self.env.user
        self._create_order(user)
        self._create_order(user, state='sent')
        self._create_order(user, confirm=True)
        self._create_order(self.other_user)
        self._create_order(self.other_user, confirm=True)
        after = self.env['sale.order'].get_dashboard_values()
        self.assertEqual(after['total_orders'] - before['total_orders'], 5)
        self.assertEqual(after['draft_orders'] - before['draft_orders'], 3)
        self.assertEqual(after['sale_orders'] - before['sale_orders'], 2)
        self.assertEqual(after['my_orders'] - before['my_orders'], 3)
        self.assertEqual(
            after['my_draft_orders'] - before['my_draft_orders'], 2)
        self.assertEqual(
            after['my_sale_orders'] - before['my_sale_orders'], 1)

    def test_dashboard_amounts(self):
        """Totals are the formatted sums of quotations and sale orders."""
        self._create_order(self.env.user)
        self._create_order(self.other_user, confirm=True)
        values = self.env['sale.order'].get_dashboard_values()
        self.assertEqual(
            values['total_sale_amount'], self._amount(['sale']))
        self.assertEqual(
            values['total_draft_amount'], self._amount(['draft', 'sent']))
