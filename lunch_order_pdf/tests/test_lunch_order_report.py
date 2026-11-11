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

from datetime import date

from odoo.exceptions import UserError
from odoo.addons.lunch.tests.common import TestsCommon


class TestLunchOrderReport(TestsCommon):

    def setUp(self):
        super().setUp()
        # Odoo 20 changes users by deriving a new Environment with env(user=...).
        self.manager_env = self.env(user=self.manager)
        self.wizard = self.manager_env['lunch.report'].create({
            'start_date': date(2021, 1, 1),
            'end_date': date(2021, 12, 31),
        })
        self.order = self.manager_env['lunch.order'].create({
            'product_id': self.product_pizza.id,
            'user_id': self.manager.id,
            'lunch_location_id': self.location_office_1.id,
            'date': date(2021, 1, 29),
        })

    def test_onchange_rejects_start_after_end(self):
        wizard = self.manager_env['lunch.report'].new({
            'start_date': date(2021, 2, 1),
            'end_date': date(2021, 1, 31),
        })
        with self.assertRaisesRegex(UserError, 'Start Date.*lesser than.*End Date'):
            wizard._onchange_date()

    def test_action_print_report_returns_matching_order(self):
        self.wizard.write({
            'user_ids': [(6, 0, self.manager.ids)],
            'lunch_supplier_ids': [(6, 0, self.supplier_pizza_inn.ids)],
            'lunch_location_ids': [(6, 0, self.location_office_1.ids)],
            'product_filter': 'category',
            'category_ids': [(6, 0, self.category_pizza.ids)],
        })

        action = self.wizard.action_print_report()

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['data']['order_ids'], self.order.ids)

    def test_action_print_report_rejects_empty_period(self):
        self.wizard.write({'start_date': date(2022, 1, 1),
                           'end_date': date(2022, 12, 31)})
        with self.assertRaisesRegex(UserError, 'There are no lunch orders'):
            self.wizard.action_print_report()

    def test_report_values_group_orders_by_user(self):
        self.wizard.group_order = 'user_id'
        report = self.manager_env['report.lunch_order_pdf.report_lunch_order']

        values = report._get_report_values(self.wizard.ids, {
            'order_ids': self.order.ids,
        })

        self.assertEqual(values['group_order'], 'user_id')
        self.assertEqual(values['grouped_orders'], [[self.manager.name, self.order]])
        self.assertTrue(values['period'].startswith('From '))

    def test_report_values_without_wizard_or_active_context(self):
        report = self.manager_env['report.lunch_order_pdf.report_lunch_order'].with_context(
            active_id=False, active_ids=False)

        values = report._get_report_values([], {'order_ids': self.order.ids})

        self.assertFalse(values['docs'])
        self.assertFalse(values['group_order'])
        self.assertEqual(values['grouped_orders'], [[False, self.order]])
        self.assertFalse(values['period'])
