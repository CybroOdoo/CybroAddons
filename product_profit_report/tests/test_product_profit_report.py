# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import timedelta
from odoo import fields

class TestProductProfitReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestProductProfitReport, cls).setUpClass()

        
        # Handle Odoo 19 specific partner constraints (autopost_bills)
        # cls.env['ir.default'].set('res.partner', 'autopost_bills', 'never')
        
        cls.company = cls.env.user.company_id
        
        # Categories
        cls.parent_category = cls.env['product.category'].create({
            'name': 'Parent Category'
        })
        cls.child_category = cls.env['product.category'].create({
            'name': 'Child Category',
            'parent_id': cls.parent_category.id
        })

        # Product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Profit Product',
            'type': 'consu',
            'categ_id': cls.child_category.id,
            'standard_price': 100.0,
            'list_price': 150.0,
        })
        
        # Create Price History
        cls.past_date = fields.Datetime.now() - timedelta(days=10)
        cls.price_history = cls.env['price.history'].create({
            'product_id': cls.product.id,
            'company_id': cls.company.id,
            'cost': 90.0,
            'datetime': cls.past_date
        })


    def test_01_get_history_price(self):
        """Test getting the historical price of a product."""

        # Getting price after history record was created
        historical_price = self.product.get_history_price(self.company.id, date=fields.Datetime.now())
        self.assertEqual(historical_price, 90.0, "The historical price retrieved should match the price history record.")
        
        # Getting price before history record was created
        older_date = self.past_date - timedelta(days=5)
        no_history_price = self.product.get_history_price(self.company.id, date=older_date)
        self.assertEqual(no_history_price, 0.0, "If no historical record exists before the given date, it should return 0.0.")

    def test_02_wizard_methods(self):
        """Test methods in the wizard."""

        wizard = self.env['profit.product'].create({
            'categ_id': self.parent_category.id,
            'from_date': fields.Date.today() - timedelta(days=30),
            'to_date': fields.Date.today()
        })

        # Test get_all_child_categories
        child_categories = wizard.get_all_child_categories(
            self.parent_category
        )

        self.assertIn(
            self.child_category.id,
            child_categories,
            "Child category should be fetched."
        )

        # Test onchange category
        wizard._onchange_categ_id()


        # Verify product inclusion
        self.assertIn(
            self.product.id,
            wizard.product_product_ids.ids,
            "The product belonging to the child category should be included."
        )

        # Test action_print_pdf_report
        action = wizard.action_print_pdf_report()

        self.assertEqual(
            action.get('type'),
            'ir.actions.report',
            "Action should be a report action."
        )


    def test_03_report_validation_error(self):
        """Test the report raises a validation error if from_date > to_date."""

        report = self.env[
            'report.product_profit_report.product_profit_report'
        ]

        data = {
            'from_date': fields.Date.today(),
            'to_date': fields.Date.today() - timedelta(days=10),
            'company_id': [self.company.id],
            'product_product_ids': [self.product.id],
            'product_id': False
        }

        with self.assertRaises(
                ValidationError,
                msg="Validation error should be raised when 'from' date is after 'to' date."
        ):
            report.generate_report_values(data)


    def test_04_report_empty_data(self):
        """Test the report generation without moves to ensure no errors."""

        report = self.env[
            'report.product_profit_report.product_profit_report'
        ]

        data = {
            'from_date': fields.Date.today() - timedelta(days=10),
            'to_date': fields.Date.today(),
            'company_id': [self.company.id],
            'product_product_ids': [self.product.id],
            'product_id': False
        }

        res = report.generate_report_values(data)


        self.assertEqual(
            res['groups'],
            {},
            "Groups should be empty when there are no accounting moves."
        )

        self.assertEqual(
            res['data'],
            data,
            "Data should be returned as passed."
        )

