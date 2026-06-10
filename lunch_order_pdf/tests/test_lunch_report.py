# -*- coding: utf-8 -*-
from datetime import date

from odoo.exceptions import UserError
from odoo.tests import common


class TestLunchReport(common.TransactionCase):

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

    def test_onchange_date_raises_for_invalid_period(self):
        wizard = self._create_wizard(
            start_date=date(2021, 1, 31),
            end_date=date(2021, 1, 1),
        )

        with self.assertRaisesRegex(UserError, "Start Date"):
            wizard._onchange_date()

    def test_action_print_report_raises_when_no_orders_match(self):
        wizard = self._create_wizard(
            start_date=date(2021, 2, 1),
            end_date=date(2021, 2, 28),
        )

        with self.assertRaisesRegex(UserError, "no lunch orders"):
            wizard.action_print_report()

    def test_action_print_report_filters_by_product(self):
        matched_order = self._create_lunch_order(
            self.product_pizza,
            date(2021, 1, 10),
            note='matched-product',
        )
        self._create_lunch_order(
            self.product_sandwich,
            date(2021, 1, 10),
            note='unmatched-product',
        )
        wizard = self._create_wizard(
            product_filter='product',
            product_ids=[(6, 0, [self.product_pizza.id])],
        )

        action = wizard.with_context(discard_logo_check=True).action_print_report()

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_name'], 'lunch_order_pdf.report_lunch_order')
        self.assertEqual(action['data'], {'order_ids': matched_order.ids})

    def test_action_print_report_filters_by_category(self):
        matched_order = self._create_lunch_order(
            self.product_sandwich,
            date(2021, 1, 12),
            note='matched-category',
        )
        self._create_lunch_order(
            self.product_pizza,
            date(2021, 1, 12),
            note='unmatched-category',
        )
        wizard = self._create_wizard(
            product_filter='category',
            category_ids=[(6, 0, [self.category_sandwich.id])],
        )

        action = wizard.with_context(discard_logo_check=True).action_print_report()

        self.assertEqual(action['data'], {'order_ids': matched_order.ids})

    def test_action_print_report_filters_by_user_supplier_location_and_company(self):
        matched_order = self._create_lunch_order(
            self.product_pizza,
            date(2021, 1, 13),
            note='matched-combined-filters',
        )
        self._create_lunch_order(
            self.product_sandwich,
            date(2021, 1, 13),
            note='unmatched-supplier',
        )
        wizard = self._create_wizard(
            user_ids=[(6, 0, [self.env.user.id])],
            company_ids=[(6, 0, [self.env.company.id])],
            lunch_supplier_ids=[(6, 0, [self.supplier_pizza.id])],
            lunch_location_ids=[(6, 0, [self.location_office.id])],
        )

        action = wizard.with_context(discard_logo_check=True).action_print_report()

        self.assertEqual(action['data'], {'order_ids': matched_order.ids})
