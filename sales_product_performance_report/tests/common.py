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
"""Shared fixtures for the performance report tests."""
from odoo import Command
from odoo.tests import TransactionCase, new_test_user


class PerformanceCommon(TransactionCase):
    """Two salesmen restricted to their own orders, one shared product."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Cancel any pre-existing sale orders in demo database so tests start with a clean slate
        cls.env['sale.order'].search([('state', '!=', 'cancel')]).write({'state': 'cancel'})

        group = 'sales_team.group_sale_salesman'
        cls.admin = cls.env.ref('base.user_admin')
        cls.alice = new_test_user(cls.env, login='perf_alice', groups=group)
        cls.bob = new_test_user(cls.env, login='perf_bob', groups=group)
        cls.partner = cls.env['res.partner'].create({'name': 'Customer'})
        cls.categ = cls.env['product.category'].create({'name': 'Perf Categ'})
        cls.product = cls.env['product.product'].create({
            'name': 'Perf Product',
            'categ_id': cls.categ.id,
            'list_price': 10.0,
            'taxes_id': [Command.clear()],
        })
        cls.alice_order = cls._make_order(cls.alice, qty=2)   # revenue 20
        cls.bob_order = cls._make_order(cls.bob, qty=3)       # revenue 30

    @classmethod
    def _make_order(cls, user, qty, date_order=None, confirm=True, **vals):
        order_vals = {
            'partner_id': cls.partner.id,
            'user_id': user.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_uom_qty': qty,
                'price_unit': 10.0,
            })],
        }
        order_vals.update(vals)
        order = cls.env['sale.order'].create(order_vals)
        if confirm:
            order.action_confirm()
        if date_order:
            order.date_order = date_order
        return order

    def _product_lines(self, user, **wizard_vals):
        """Run the product wizard as ``user`` and return the lines."""
        vals = {
            'categ_id': self.categ.id,
            'up_to_date_report': True,
            'product_ids': [Command.set(self.product.product_tmpl_id.ids)],
        }
        vals.update(wizard_vals)
        wizard = self.env['product.performance'].with_user(user).create(vals)
        action = wizard.action_product_performance()
        self.assertEqual(action['res_model'], 'product.performance.line')
        return self.env['product.performance.line'].with_user(user).search(
            action['domain'])

    def _sales_lines(self, user, persons=None, **wizard_vals):
        """Run the sales wizard as ``user`` and return the lines."""
        vals = {'up_to_date_report': True}
        if persons:
            vals['sales_person_ids'] = [Command.set(persons.ids)]
        vals.update(wizard_vals)
        wizard = self.env['sales.performance'].with_user(user).create(vals)
        action = wizard.action_sales_performance()
        self.assertEqual(action['res_model'], 'sales.performance.line')
        return self.env['sales.performance.line'].with_user(user).search(
            action['domain'])
