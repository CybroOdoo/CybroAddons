# -*- coding: utf-8 -*-
from datetime import date

from odoo.tests import common


class TestLunchOrderReport(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['lunch.cashmove'].create({'amount': 100})
        self.location_office = self.env['lunch.location'].create({
            'name': 'Test Office',
        })
        self.category_pizza = self.env['lunch.product.category'].create({
            'name': 'Test Pizza Category',
        })
        self.category_sandwich = self.env['lunch.product.category'].create({
            'name': 'Test Sandwich Category',
        })
        partner_pizza = self.env.company.partner_id
        partner_sandwich = self.env['res.partner'].search([
            ('id', '!=', partner_pizza.id),
        ], limit=1)
        self.supplier_pizza = self.env['lunch.supplier'].create({
            'partner_id': partner_pizza.id,
            'name': 'Test Pizza Supplier',
        })
        self.supplier_sandwich = self.env['lunch.supplier'].create({
            'partner_id': partner_sandwich.id,
            'name': 'Test Sandwich Supplier',
        })
        self.product_pizza = self.env['lunch.product'].create({
            'name': 'Test Pizza',
            'category_id': self.category_pizza.id,
            'price': 9,
            'supplier_id': self.supplier_pizza.id,
        })
        self.product_sandwich = self.env['lunch.product'].create({
            'name': 'Test Sandwich',
            'category_id': self.category_sandwich.id,
            'price': 3,
            'supplier_id': self.supplier_sandwich.id,
        })

    def _create_lunch_order(self, product, order_date, **values):
        vals = {
            'product_id': product.id,
            'user_id': self.env.user.id,
            'lunch_location_id': self.location_office.id,
            'date': order_date,
            'note': '%s-%s' % (product.name, order_date),
        }
        vals.update(values)
        return self.env['lunch.order'].create(vals)

    def _create_wizard(self, **values):
        vals = {
            'start_date': date(2021, 1, 1),
            'end_date': date(2021, 1, 31),
        }
        vals.update(values)
        return self.env['lunch.report'].create(vals)

    def _get_report_values(self, wizard, orders):
        return self.env['report.lunch_order_pdf.report_lunch_order'].with_context(
            active_id=wizard.id,
            lang='en_US',
        )._get_report_values([], data={'order_ids': orders.ids})

    def test_get_report_values_without_grouping(self):
        orders = self._create_lunch_order(
            self.product_pizza,
            date(2021, 1, 10),
            note='ungrouped',
        )
        wizard = self._create_wizard()

        values = self._get_report_values(wizard, orders)

        self.assertEqual(values['docs'], wizard)
        self.assertFalse(values['group_order'])
        self.assertEqual(values['grouped_orders'], [[False, orders]])
        self.assertEqual(values['period'], 'From 01/01/2021 To 01/31/2021')

    def test_get_report_values_groups_by_user(self):
        order = self._create_lunch_order(
            self.product_pizza,
            date(2021, 1, 10),
            note='user-group',
        )
        wizard = self._create_wizard(group_order='user_id')

        grouped_orders = self._get_report_values(wizard, order)['grouped_orders']

        self.assertEqual(grouped_orders, [[self.env.user.name, order]])

    def test_get_report_values_groups_by_supplier(self):
        order_pizza = self._create_lunch_order(
            self.product_pizza,
            date(2021, 1, 10),
            note='pizza-supplier',
        )
        order_sandwich = self._create_lunch_order(
            self.product_sandwich,
            date(2021, 1, 11),
            note='sandwich-supplier',
        )
        wizard = self._create_wizard(group_order='supplier_id')

        grouped_orders = self._get_report_values(wizard, order_pizza | order_sandwich)['grouped_orders']

        self.assertEqual([group[0] for group in grouped_orders], ['Test Pizza Supplier', 'Test Sandwich Supplier'])
        self.assertEqual(grouped_orders[0][1], order_pizza)
        self.assertEqual(grouped_orders[1][1], order_sandwich)

    def test_get_report_values_groups_by_product(self):
        order_pizza = self._create_lunch_order(
            self.product_pizza,
            date(2021, 1, 10),
            note='pizza-product',
        )
        order_sandwich = self._create_lunch_order(
            self.product_sandwich,
            date(2021, 1, 11),
            note='sandwich-product',
        )
        wizard = self._create_wizard(group_order='product_id')

        grouped_orders = self._get_report_values(wizard, order_pizza | order_sandwich)['grouped_orders']

        self.assertEqual([group[0] for group in grouped_orders], ['Test Pizza', 'Test Sandwich'])
        self.assertEqual(grouped_orders[0][1], order_pizza)
        self.assertEqual(grouped_orders[1][1], order_sandwich)

    def test_get_report_values_groups_by_state_in_report_order(self):
        order_new = self._create_lunch_order(
            self.product_pizza,
            date(2021, 1, 10),
            state='new',
            note='new-state',
        )
        order_ordered = self._create_lunch_order(
            self.product_sandwich,
            date(2021, 1, 11),
            state='ordered',
            note='ordered-state',
        )
        order_cancelled = self._create_lunch_order(
            self.product_pizza,
            date(2021, 1, 12),
            state='cancelled',
            note='cancelled-state',
        )
        wizard = self._create_wizard(group_order='state')

        grouped_orders = self._get_report_values(
            wizard,
            order_cancelled | order_ordered | order_new,
        )['grouped_orders']

        self.assertEqual([group[0] for group in grouped_orders], ['new', 'ordered', 'cancelled'])
        self.assertEqual(grouped_orders[0][1], order_new)
        self.assertEqual(grouped_orders[1][1], order_ordered)
        self.assertEqual(grouped_orders[2][1], order_cancelled)

    def test_get_report_values_groups_by_company(self):
        order = self._create_lunch_order(
            self.product_pizza,
            date(2021, 1, 10),
            note='company-group',
        )
        wizard = self._create_wizard(group_order='company_id')

        grouped_orders = self._get_report_values(wizard, order)['grouped_orders']

        self.assertEqual(grouped_orders, [[self.env.company.name, order]])
