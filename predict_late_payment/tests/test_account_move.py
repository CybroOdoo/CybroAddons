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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for account.move payment risk extensions."""
from datetime import date, timedelta
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAccountMovePaymentRisk(TransactionCase):
    """Test suite covering payment risk computations on account.move."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Invoice Test Customer',
            'customer_rank': 1,
            'email': 'inv_cust@example.com',
        })
        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].create({
                'name': 'Test Income Move',
                'code': 'INC_TEST_MOVE',
                'account_type': 'income',
            })

    def _create_invoice(self, move_type='out_invoice', invoice_date=None, due_date=None):
        today = date.today()
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner.id,
            'invoice_date': invoice_date or today,
            'invoice_date_due': due_date or today,
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Item',
                    'quantity': 1,
                    'price_unit': 500.0,
                    'account_id': self.income_account.id,
                })
            ]
        })
        return invoice

    def test_compute_invoice_risk_without_score(self):
        """Test compute_invoice_risk when partner has no risk score record."""
        invoice = self._create_invoice()
        invoice._compute_invoice_risk()
        self.assertEqual(invoice.invoice_payment_risk_score, 0.0)
        self.assertFalse(invoice.invoice_payment_risk_level)
        self.assertEqual(invoice.invoice_payment_risk_color, '#6c757d')

    def test_compute_invoice_risk_with_score(self):
        """Test compute_invoice_risk when partner has a risk score record."""
        self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'score': 85.0,
        })
        invoice = self._create_invoice()
        invoice._compute_invoice_risk()
        self.assertEqual(invoice.invoice_payment_risk_score, 85.0)
        self.assertEqual(invoice.invoice_payment_risk_level, 'critical')
        self.assertEqual(invoice.invoice_payment_risk_color, '#dc3545')

    def test_compute_invoice_risk_non_out_invoice(self):
        """Test compute_invoice_risk on bills/in_invoice sets default zero risk."""
        self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'score': 70.0,
        })
        expense_account = self.env['account.account'].search([
            ('account_type', '=', 'expense'),
        ], limit=1)
        if not expense_account:
            expense_account = self.env['account.account'].create({
                'name': 'Test Expense Move',
                'code': 'EXP_TEST_MOVE',
                'account_type': 'expense',
            })
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_date': date.today(),
            'invoice_date_due': date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Expense Item',
                'price_unit': 200.0,
                'account_id': expense_account.id,
            })]
        })
        bill._compute_invoice_risk()
        self.assertEqual(bill.invoice_payment_risk_score, 0.0)
        self.assertFalse(bill.invoice_payment_risk_level)

    def test_invoice_days_overdue(self):
        """Test days overdue calculation for overdue and non-overdue invoices."""
        today = date.today()
        # Overdue invoice: 15 days overdue
        inv_overdue = self._create_invoice(
            invoice_date=today - timedelta(days=30),
            due_date=today - timedelta(days=15),
        )
        inv_overdue.action_post()
        inv_overdue._compute_invoice_risk()
        self.assertEqual(inv_overdue.invoice_days_overdue, 15)

        # Future due date: 0 days overdue
        inv_future = self._create_invoice(
            invoice_date=today,
            due_date=today + timedelta(days=10),
        )
        inv_future._compute_invoice_risk()
        self.assertEqual(inv_future.invoice_days_overdue, 0)

    def test_get_last_payment_date_no_reconciled_payments(self):
        """Test _get_last_payment_date returns None when invoice has no payments."""
        invoice = self._create_invoice()
        invoice.action_post()
        self.assertIsNone(invoice._get_last_payment_date())

    def test_action_compute_partner_risk(self):
        """Test button action action_compute_partner_risk recalculates score and returns notification."""
        invoice = self._create_invoice()
        action = invoice.action_compute_partner_risk()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')
        self.assertEqual(action['params']['type'], 'success')

        # Partner now has a risk score record
        score_rec = self.env['payment.risk.score'].search([
            ('partner_id', '=', self.partner.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertTrue(score_rec)

    def test_action_compute_partner_risk_invoice_user(self):
        """Test invoice user with read-only risk score access can compute risk from invoice."""
        invoice = self._create_invoice()
        invoice_group = self.env.ref('account.group_account_invoice')
        user = self.env['res.users'].create({
            'name': 'Invoice User Account Move',
            'login': 'invoice_user_move_test',
            'email': 'invoice_user_move@example.com',
            'group_ids': [(6, 0, [invoice_group.id, self.env.ref('base.group_user').id])],
        })
        action = invoice.with_user(user).action_compute_partner_risk()
        self.assertEqual(action.get('params', {}).get('type'), 'success')
