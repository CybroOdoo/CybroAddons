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
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import fields, Command
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLoanManagement(TransactionCase):
    """Test suite covering loan types, requests, approvals, disbursements, repayments, and reports."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'John Doe',
            'email': 'johndoe@example.com',
            'street': '123 Main St',
            'city': 'Metropolis',
            'phone': '+1234567890',
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Jane Smith',
            'email': 'janesmith@example.com',
        })

        cls.document = cls.env['loan.documents'].create({
            'loan_proofs': 'Passport',
        })

        cls.loan_type = cls.env['loan.type'].create({
            'name': 'Personal Loan 12M',
            'loan_amount': 12000.0,
            'tenure': 12,
            'interest_rate': 0.10,
            'processing_fee': 500,
            'documents_ids': [Command.link(cls.document.id)],
        })

        cls.disburse_journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.disburse_journal:
            cls.disburse_journal = cls.env['account.journal'].create({
                'name': 'Disburse Test Journal',
                'code': 'TDIST',
                'type': 'purchase',
                'company_id': cls.company.id,
            })

        cls.debit_account = cls.env['account.account'].search([
            ('account_type', '=', 'liability_current'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.debit_account:
            cls.debit_account = cls.env['account.account'].create({
                'name': 'Test Loan Disburse Debit',
                'code': '200099',
                'account_type': 'liability_current',
                'company_ids': [Command.link(cls.company.id)],
            })

        cls.credit_account = cls.env['account.account'].search([
            ('account_type', 'in', ('asset_current', 'asset_cash')),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.credit_account:
            cls.credit_account = cls.env['account.account'].create({
                'name': 'Test Loan Disburse Credit',
                'code': '100099',
                'account_type': 'asset_cash',
                'company_ids': [Command.link(cls.company.id)],
            })

    def test_01_loan_type_disbursal_amount(self):
        """Verify loan type computes disbursal amount correctly."""
        self.assertEqual(self.loan_type.disbursal_amount, 11500.0)
        self.loan_type.processing_fee = 1000
        self.assertEqual(self.loan_type.disbursal_amount, 11000.0)

    def test_02_loan_request_creation_and_partner_validation(self):
        """Verify sequence generation, currency default, and active loan restriction."""
        loan_1 = self.env['loan.request'].create({
            'partner_id': self.partner.id,
            'loan_type_id': self.loan_type.id,
        })
        self.assertNotEqual(loan_1.name, 'New')
        self.assertEqual(loan_1.currency_id, self.company.currency_id)
        self.assertEqual(loan_1.state, 'draft')

        # Confirming loan_1 makes it active
        loan_1.action_loan_request()
        self.assertEqual(loan_1.state, 'confirmed')

        # Creating another loan for the same partner must raise UserError
        with self.assertRaises(UserError) as cm:
            self.env['loan.request'].create({
                'partner_id': self.partner.id,
                'loan_type_id': self.loan_type.id,
            })
        self.assertIn('already has an ongoing loan', str(cm.exception))

    def test_03_repayment_computation_and_loan_workflow(self):
        """Verify repayment schedule computation, approval, disbursement, and partner count."""
        loan = self.env['loan.request'].create({
            'partner_id': self.partner.id,
            'loan_type_id': self.loan_type.id,
            'journal_id': self.disburse_journal.id,
            'debit_account_id': self.debit_account.id,
            'credit_account_id': self.credit_account.id,
        })
        loan.action_loan_request()

        # Cannot request without computing repayments
        action_popup = loan.action_request_for_loan()
        self.assertEqual(action_popup.get('res_model'), 'message.popup')
        self.assertEqual(loan.state, 'confirmed')

        # Compute repayments
        loan.action_compute_repayment()
        self.assertTrue(loan.request)
        self.assertEqual(len(loan.repayment_lines_ids), 12)

        line_1 = loan.repayment_lines_ids[0]
        self.assertAlmostEqual(line_1.amount, 1000.0)
        self.assertAlmostEqual(line_1.interest_amount, 100.0)
        self.assertAlmostEqual(line_1.total_amount, 1100.0)
        self.assertEqual(line_1.state, 'unpaid')

        # Request loan
        loan.action_request_for_loan()
        self.assertEqual(loan.state, 'waiting')

        # Approve loan
        loan.action_loan_approved()
        self.assertEqual(loan.state, 'approved')

        # Disburse loan
        loan.action_disburse_loan()
        self.assertEqual(loan.state, 'disbursed')
        disburse_move = self.env['account.move'].search([('ref', '=', loan.name)], limit=1)
        self.assertTrue(disburse_move)
        self.assertEqual(disburse_move.state, 'posted')

        # Verify partner loan count
        self.assertEqual(self.partner.loan_count, 1)

    def test_04_repayment_lines_invoicing_and_state_transitions(self):
        """Verify EMI invoicing, chronological payment order, and move draft/cancel sync."""
        loan = self.env['loan.request'].create({
            'partner_id': self.partner.id,
            'loan_type_id': self.loan_type.id,
            'journal_id': self.disburse_journal.id,
            'debit_account_id': self.debit_account.id,
            'credit_account_id': self.credit_account.id,
        })
        loan.action_loan_request()
        loan.action_compute_repayment()
        loan.action_request_for_loan()
        loan.action_loan_approved()
        loan.action_disburse_loan()

        lines = loan.repayment_lines_ids.sorted(lambda l: l.date)
        line_1 = lines[0]
        line_2 = lines[1]

        # Paying line 2 before line 1 should be blocked
        warn_action = line_2.action_pay_emi()
        self.assertEqual(warn_action.get('res_model'), 'message.popup')

        # Pay line 1
        inv_action = line_1.action_pay_emi()
        self.assertEqual(line_1.state, 'invoiced')
        self.assertTrue(line_1.invoice)

        invoice = self.env['account.move'].browse(inv_action['res_id'])
        self.assertEqual(invoice.repayment_line_id, line_1)
        self.assertEqual(invoice.state, 'posted')

        # View invoice action
        view_action = line_1.action_view_invoice()
        self.assertEqual(view_action['res_id'], invoice.id)

        # Reset invoice to draft
        invoice.button_draft()
        self.assertEqual(line_1.state, 'invoiced')

        # Cancel invoice
        invoice.button_cancel()
        self.assertEqual(line_1.state, 'unpaid')
        self.assertFalse(line_1.invoice)

        # Register payment on invoice via account.payment.register
        line_1.action_pay_emi()
        new_inv = self.env['account.move'].search([('repayment_line_id', '=', line_1.id)], order='id desc', limit=1)
        action_data = new_inv.action_register_payment()
        payment_register = self.env['account.payment.register'].with_context(
            **action_data['context']
        ).create({})
        payment_register._create_payments()
        self.assertEqual(line_1.state, 'paid')

    def test_05_loan_closure_and_rejection_wizard(self):
        """Verify loan cannot close with unpaid repayments and reject reason wizard."""
        loan = self.env['loan.request'].create({
            'partner_id': self.partner_2.id,
            'loan_type_id': self.loan_type.id,
            'journal_id': self.disburse_journal.id,
            'debit_account_id': self.debit_account.id,
            'credit_account_id': self.credit_account.id,
        })
        loan.action_loan_request()
        loan.action_compute_repayment()
        loan.action_request_for_loan()

        # Reject reason wizard
        wizard = self.env['reject.reason'].create({
            'loan': loan.name,
            'reason': 'Credit score insufficient',
        })
        wizard.action_reject_reason_txt()
        self.assertEqual(loan.state, 'rejected')
        self.assertEqual(loan.reject_reason, 'Credit score insufficient')

        # Once rejected, partner 2 can request another loan
        loan_new = self.env['loan.request'].create({
            'partner_id': self.partner_2.id,
            'loan_type_id': self.loan_type.id,
            'journal_id': self.disburse_journal.id,
            'debit_account_id': self.debit_account.id,
            'credit_account_id': self.credit_account.id,
        })
        loan_new.action_loan_request()
        loan_new.action_compute_repayment()
        loan_new.action_request_for_loan()
        loan_new.action_loan_approved()
        loan_new.action_disburse_loan()

        # Cannot close while lines unpaid
        close_popup = loan_new.action_close_loan()
        self.assertEqual(close_popup.get('res_model'), 'message.popup')
        self.assertEqual(loan_new.state, 'disbursed')

        # Mark all paid and close
        loan_new.repayment_lines_ids.write({'state': 'paid'})
        loan_new.action_close_loan()
        self.assertEqual(loan_new.state, 'closed')

    def test_06_report_values_singleton_safety(self):
        """Verify report values computation handles single, multiple, and empty doc_ids."""
        loan = self.env['loan.request'].create({
            'partner_id': self.partner.id,
            'loan_type_id': self.loan_type.id,
        })
        loan.action_loan_request()
        loan.action_compute_repayment()

        report_model = self.env['report.advanced_loan_management.loan_report_template']

        # Normal single record
        values_single = report_model._get_report_values(loan.ids)
        self.assertEqual(values_single['data']['Customer'], self.partner.name)
        self.assertEqual(len(values_single['docs']), 12)

        # Multi-record doc_ids (graceful fallback)
        values_multi = report_model._get_report_values(loan.ids + [999999])
        self.assertEqual(values_multi['data']['Customer'], self.partner.name)

        # Empty doc_ids
        values_empty = report_model._get_report_values([])
        self.assertEqual(values_empty['data']['Customer'], '')
        self.assertEqual(values_empty['docs'], [])
