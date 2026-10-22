# -*- coding: utf-8 -*-
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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import timedelta
from odoo import fields, Command
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAdvancedPosReports(TransactionCase):
    """Comprehensive test suite for Advanced POS Reports module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        layout = cls.env.ref('web.external_layout_standard', raise_if_not_found=False)
        if layout:
            cls.company.external_report_layout_id = layout.id
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test POS Customer',
            'email': 'pos_customer@test.com',
        })
        cls.pos_category = cls.env['pos.category'].create({
            'name': 'Test POS Category',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test POS Product',
            'default_code': 'TP01',
            'is_storable': True,
            'available_in_pos': True,
            'list_price': 25.0,
            'pos_categ_ids': [Command.link(cls.pos_category.id)],
        })
        cls.non_pos_product = cls.env['product.product'].create({
            'name': 'Non POS Product',
            'is_storable': True,
            'available_in_pos': False,
            'list_price': 50.0,
        })
        cls.stock_location = cls.env['stock.location'].create({
            'name': 'Internal POS Location',
            'usage': 'internal',
        })
        cls.env['stock.quant'].create({
            'product_id': cls.product.id,
            'location_id': cls.stock_location.id,
            'quantity': 100.0,
        })
        cls.env['stock.quant'].create({
            'product_id': cls.non_pos_product.id,
            'location_id': cls.stock_location.id,
            'quantity': 40.0,
        })

        cls.payment_method = cls.env['pos.payment.method'].create({
            'name': 'Cash Test Method',
            'type': 'cash',
            'company_id': cls.company.id,
        })

        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Main Store POS',
            'payment_method_ids': [Command.link(cls.payment_method.id)],
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
            'name': 'POS/Session/Test-20.0',
        })
        cls.pos_session.write({'state': 'opened'})

        order_date = fields.Datetime.now()
        cls.pos_order = cls.env['pos.order'].create({
            'name': 'POS/TEST/001',
            'session_id': cls.pos_session.id,
            'partner_id': cls.partner.id,
            'date_order': order_date,
            'lines': [Command.create({
                'product_id': cls.product.id,
                'qty': 4.0,
                'price_unit': 25.0,
                'price_subtotal': 100.0,
                'price_subtotal_incl': 100.0,
            })],
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 100.0,
            'amount_return': 0.0,
            'state': 'paid',
        })
        cls.pos_payment = cls.env['pos.payment'].create({
            'pos_order_id': cls.pos_order.id,
            'payment_method_id': cls.payment_method.id,
            'amount': 100.0,
            'session_id': cls.pos_session.id,
        })

        cls.pos_return_order = cls.env['pos.order'].create({
            'name': 'POS/TEST/002_RETURN',
            'session_id': cls.pos_session.id,
            'partner_id': cls.partner.id,
            'date_order': order_date,
            'lines': [Command.create({
                'product_id': cls.product.id,
                'qty': -1.0,
                'price_unit': 25.0,
                'price_subtotal': -25.0,
                'price_subtotal_incl': -25.0,
            })],
            'amount_total': -25.0,
            'amount_tax': 0.0,
            'amount_paid': -25.0,
            'amount_return': 0.0,
            'state': 'paid',
        })
        cls.pos_return_payment = cls.env['pos.payment'].create({
            'pos_order_id': cls.pos_return_order.id,
            'payment_method_id': cls.payment_method.id,
            'amount': -25.0,
            'session_id': cls.pos_session.id,
        })

    def test_pos_config_get_location_summary(self):
        """Test PosConfig.get_location_summary returns only POS-available products."""
        summary = self.env['pos.config'].get_location_summary(self.stock_location.id)
        self.assertTrue(len(summary) >= 1)
        product_ids = [item['product_id'] for item in summary]
        self.assertIn(self.product.id, product_ids)
        self.assertNotIn(self.non_pos_product.id, product_ids)

        product_item = next(item for item in summary if item['product_id'] == self.product.id)
        self.assertEqual(product_item['quantity'], 100.0)

    def test_pos_session_load_pos_data_models(self):
        """Test PosSession._load_pos_data_models appends stock.location."""
        models_list = self.env['pos.session']._load_pos_data_models(self.pos_config)
        self.assertIn('stock.location', models_list)

    def test_stock_location_pos_mixin(self):
        """Test StockLocation pos.load.mixin methods."""
        domain = self.env['stock.location']._load_pos_data_domain({})
        self.assertEqual(domain, [('usage', '=', 'internal')])

        fields_list = self.env['stock.location']._load_pos_data_fields(self.pos_config)
        self.assertIn('id', fields_list)
        self.assertIn('name', fields_list)

    def test_pos_order_category_summary(self):
        """Test PosOrder.get_category_summary SQL aggregation."""
        summary = self.env['pos.order'].get_category_summary([self.pos_order.id])
        self.assertTrue(len(summary) >= 1)
        categ_entry = summary[0]
        self.assertEqual(categ_entry['id'], self.pos_category.id)
        self.assertEqual(categ_entry['name'], self.pos_category.name)
        self.assertEqual(categ_entry['qty'], 4.0)
        self.assertEqual(categ_entry['amount'], 100.0)

        empty_summary = self.env['pos.order'].get_category_summary([])
        self.assertEqual(empty_summary, [])

    def test_pos_order_product_summary(self):
        """Test PosOrder.get_product_summary SQL aggregation."""
        summary = self.env['pos.order'].get_product_summary([self.pos_order.id])
        self.assertTrue(len(summary) >= 1)
        prod_entry = summary[0]
        self.assertEqual(prod_entry['id'], self.product.id)
        self.assertEqual(prod_entry['name'], self.product.name)
        self.assertEqual(prod_entry['code'], 'TP01')
        self.assertEqual(prod_entry['qty'], 4.0)

        empty_summary = self.env['pos.order'].get_product_summary([])
        self.assertEqual(empty_summary, [])

    def test_pos_order_order_summary(self):
        """Test PosOrder.get_order_summary mapping."""
        summary = self.env['pos.order'].get_order_summary([self.pos_order.id])
        self.assertEqual(len(summary), 1)
        order_entry = summary[0]
        self.assertEqual(order_entry['order_name'], self.pos_order.name)
        self.assertEqual(order_entry['amount_total'], 100.0)
        self.assertEqual(order_entry['id'], self.pos_order.id)

        empty_summary = self.env['pos.order'].get_order_summary([])
        self.assertEqual(empty_summary, [])

    def test_pos_payment_payment_summary(self):
        """Test PosPayment.get_payment_summary SQL aggregation."""
        summary = self.env['pos.payment'].get_payment_summary([self.pos_order.id])
        self.assertTrue(len(summary) >= 1)
        pay_entry = summary[0]
        self.assertEqual(pay_entry['id'], self.payment_method.id)
        self.assertEqual(pay_entry['name'], self.payment_method.name)
        self.assertEqual(pay_entry['total'], 100.0)

        empty_summary = self.env['pos.payment'].get_payment_summary([])
        self.assertEqual(empty_summary, [])

    def test_pos_sale_ongoing_wizard(self):
        """Test PosSaleOngoing wizard report generation."""
        wizard = self.env['pos.sale.ongoing'].with_context(discard_logo_check=True).create({
            'session_ids': [Command.link(self.pos_session.id)],
        })
        action = wizard.action_generate_report()
        self.assertEqual(
            action.get('report_name'),
            'advanced_pos_reports.report_pos_ongoing_session'
        )
        self.assertIn(self.pos_session.id, action.get('data', {}).get('session_ids', []))

    def test_pos_sale_top_selling_wizard_validations(self):
        """Test PosSaleTopSelling wizard validation errors."""
        now = fields.Datetime.now()
        # End date before start date
        with self.assertRaises(ValidationError):
            wizard = self.env['pos.sale.top.selling'].create({
                'start_date': now + timedelta(days=1),
                'end_date': now,
                'top_selling': 'products',
            })
            wizard.action_generate_report()

        # No orders in range
        with self.assertRaises(ValidationError):
            wizard = self.env['pos.sale.top.selling'].create({
                'start_date': now - timedelta(days=50),
                'end_date': now - timedelta(days=40),
                'top_selling': 'products',
            })
            wizard.action_generate_report()

    def test_pos_sale_top_selling_wizard_actions(self):
        """Test PosSaleTopSelling wizard for products, category, and customers."""
        now = fields.Datetime.now()
        start = now - timedelta(days=1)
        end = now + timedelta(days=1)

        # Products
        wizard_prod = self.env['pos.sale.top.selling'].with_context(discard_logo_check=True).create({
            'start_date': start,
            'end_date': end,
            'top_selling': 'products',
            'no_of_products': 5,
        })
        action_prod = wizard_prod.action_generate_report()
        self.assertEqual(
            action_prod.get('report_name'),
            'advanced_pos_reports.report_pos_top_selling_products'
        )
        self.assertTrue(len(action_prod.get('data', {}).get('products', [])) >= 1)

        # Categories
        wizard_categ = self.env['pos.sale.top.selling'].with_context(discard_logo_check=True).create({
            'start_date': start,
            'end_date': end,
            'top_selling': 'category',
            'no_of_categories': 5,
        })
        action_categ = wizard_categ.action_generate_report()
        self.assertEqual(
            action_categ.get('report_name'),
            'advanced_pos_reports.report_pos_top_selling_categories'
        )
        self.assertTrue(len(action_categ.get('data', {}).get('categories', [])) >= 1)

        # Customers
        wizard_cust = self.env['pos.sale.top.selling'].with_context(discard_logo_check=True).create({
            'start_date': start,
            'end_date': end,
            'top_selling': 'customers',
            'no_of_customers': 5,
        })
        action_cust = wizard_cust.action_generate_report()
        self.assertEqual(
            action_cust.get('report_name'),
            'advanced_pos_reports.report_pos_top_selling_customers'
        )
        self.assertTrue(len(action_cust.get('data', {}).get('customers', [])) >= 1)

    def test_report_pos_ongoing_session_values(self):
        """Test ReportPosOngoingSession calculation and report values."""
        report = self.env['report.advanced_pos_reports.report_pos_ongoing_session']
        values = report._get_report_values([], data={'session_ids': [self.pos_session.id]})
        self.assertIn('sessions', values)
        self.assertIn('categories', values)
        self.assertIn('payments', values)
        self.assertIn('total_paid', values)
        self.assertEqual(values['amount_total_without_tax'], 75.0)
        self.assertEqual(values['amount_total'], 75.0)
        self.assertEqual(values['amount_return'], -25.0)

    def test_report_pos_top_selling_products_values(self):
        """Test ReportPosTopSellingProducts calculation and report values."""
        now = fields.Datetime.now()
        report = self.env['report.advanced_pos_reports.report_pos_top_selling_products']
        values = report._get_report_values([], data={
            'start_date': now - timedelta(days=1),
            'end_date': now + timedelta(days=1),
            'no_of_products': 5,
        })
        self.assertIn('products', values)
        self.assertTrue(len(values['products']) >= 1)

        # Test branch without no_of_products limit
        values_no_limit = report._get_report_values([], data={
            'start_date': now - timedelta(days=1),
            'end_date': now + timedelta(days=1),
        })
        self.assertIn('products', values_no_limit)

    def test_report_pos_top_selling_categories_values(self):
        """Test ReportPosTopSellingCategories calculation and report values."""
        now = fields.Datetime.now()
        report = self.env['report.advanced_pos_reports.report_pos_top_selling_categories']
        values = report._get_report_values([], data={
            'start_date': now - timedelta(days=1),
            'end_date': now + timedelta(days=1),
            'no_of_categories': 5,
        })
        self.assertIn('categories', values)
        self.assertTrue(len(values['categories']) >= 1)

        # Test branch without no_of_categories limit
        values_no_limit = report._get_report_values([], data={
            'start_date': now - timedelta(days=1),
            'end_date': now + timedelta(days=1),
        })
        self.assertIn('categories', values_no_limit)

    def test_report_pos_top_selling_customers_values(self):
        """Test ReportPosTopSellingCustomers calculation and report values."""
        now = fields.Datetime.now()
        report = self.env['report.advanced_pos_reports.report_pos_top_selling_customers']
        values = report._get_report_values([], data={
            'start_date': now - timedelta(days=1),
            'end_date': now + timedelta(days=1),
            'no_of_customers': 5,
        })
        self.assertIn('customers', values)
        self.assertTrue(len(values['customers']) >= 1)

        # Test branch without no_of_customers limit
        values_no_limit = report._get_report_values([], data={
            'start_date': now - timedelta(days=1),
            'end_date': now + timedelta(days=1),
        })
        self.assertIn('customers', values_no_limit)
