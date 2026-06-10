# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import logging
from odoo import fields
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)

class TestAccountMoveDashboard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountMoveDashboard, cls).setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.journal_sale = cls.env['account.journal'].search([
            ('type', '=', 'sale'), ('company_id', '=', cls.company.id)
        ], limit=1)
        cls.journal_purchase = cls.env['account.journal'].search([
            ('type', '=', 'purchase'), ('company_id', '=', cls.company.id)
        ], limit=1)

        # Create a simple account for lines
        cls.account_revenue = cls.env['account.account'].search([
            ('account_type', '=', 'income'), ('company_ids', 'in', cls.company.id)
        ], limit=1)
        if not cls.account_revenue:
            cls.account_revenue = cls.env['account.account'].create({
                'name': 'Test Revenue',
                'code': 'REV_TEST',
                'account_type': 'income',
                'company_ids': [(6, 0, [cls.company.id])],
            })
            
        cls.account_expense = cls.env['account.account'].search([
            ('account_type', '=', 'expense'), ('company_ids', 'in', cls.company.id)
        ], limit=1)
        if not cls.account_expense:
            cls.account_expense = cls.env['account.account'].create({
                'name': 'Test Expense',
                'code': 'EXP_TEST',
                'account_type': 'expense',
                'company_ids': [(6, 0, [cls.company.id])],
            })

        # Create an out_invoice
        cls.out_invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_date': fields.Date.today(),
            'journal_id': cls.journal_sale.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test product sale',
                'quantity': 1,
                'price_unit': 100.0,
                'account_id': cls.account_revenue.id,
            })]
        })

        # Create an in_invoice
        cls.in_invoice = cls.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': cls.partner.id,
            'invoice_date': fields.Date.today(),
            'journal_id': cls.journal_purchase.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test product purchase',
                'quantity': 1,
                'price_unit': 150.0,
                'account_id': cls.account_expense.id,
            })]
        })

    def test_retrieve_out_invoice_dashboard(self):
        """Test retrieving out invoice dashboard values."""
        _logger.info("Starting test_retrieve_out_invoice_dashboard")
        res_draft = self.env['account.move'].retrieve_out_invoice_dashboard()
        self.assertTrue(isinstance(res_draft, dict))
        
        _logger.info("Posting out_invoice")
        self.out_invoice.action_post()
        
        _logger.info("Retrieving out_invoice dashboard after post")
        res_posted = self.env['account.move'].retrieve_out_invoice_dashboard()
        self.assertTrue(isinstance(res_posted, dict))
        
        expected_keys = [
            'draft', 'posted', 'cancelled', 'paid', 'not_paid_amount',
            'paid_amount', 'lost_amount', 'expected_amount', 'company_currency_symbol'
        ]
        for key in expected_keys:
            self.assertIn(key, res_posted)
            
        # Test with context default_move_type
        res_context = self.env['account.move'].with_context(default_move_type='out_invoice').retrieve_out_invoice_dashboard()
        self.assertTrue(isinstance(res_context, dict))

        # Test with domain
        res_domain = self.env['account.move'].retrieve_out_invoice_dashboard(domain=[('move_type', '=', 'out_invoice')])
        self.assertTrue(isinstance(res_domain, dict))


    def test_retrieve_in_invoice_dashboard(self):
        """Test retrieving in invoice dashboard values."""
        _logger.info("Starting test_retrieve_in_invoice_dashboard")
        res_draft = self.env['account.move'].retrieve_in_invoice_dashboard()
        self.assertTrue(isinstance(res_draft, dict))
        
        _logger.info("Posting in_invoice")
        self.in_invoice.action_post()
        
        _logger.info("Retrieving in_invoice dashboard after post")
        res_posted = self.env['account.move'].retrieve_in_invoice_dashboard()
        self.assertTrue(isinstance(res_posted, dict))
        
        expected_keys = [
            'draft', 'posted', 'cancelled', 'paid', 'not_paid_amount',
            'paid_amount', 'lost_amount', 'expected_amount', 'company_currency_symbol'
        ]
        for key in expected_keys:
            self.assertIn(key, res_posted)

        # Test with context default_move_type
        res_context = self.env['account.move'].with_context(default_move_type='in_invoice').retrieve_in_invoice_dashboard()
        self.assertTrue(isinstance(res_context, dict))

        # Test with domain
        res_domain = self.env['account.move'].retrieve_in_invoice_dashboard(domain=[('move_type', '=', 'in_invoice')])
        self.assertTrue(isinstance(res_domain, dict))

