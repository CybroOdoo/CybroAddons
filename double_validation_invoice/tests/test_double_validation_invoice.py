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
from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'double_validation_invoice')
class TestDoubleValidationInvoice(TransactionCase):
    """Test suite for Double Validation of Invoice and Bill."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Invoice Partner',
        })

        cls.journal_sale = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.journal_sale:
            cls.journal_sale = cls.env['account.journal'].create({
                'name': 'Customer Invoices Test',
                'code': 'TSINV',
                'type': 'sale',
                'company_id': cls.company.id,
            })

        cls.journal_misc = cls.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.journal_misc:
            cls.journal_misc = cls.env['account.journal'].create({
                'name': 'Misc Test Journal',
                'code': 'TMISC',
                'type': 'general',
                'company_id': cls.company.id,
            })

        cls.account_income = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.account_income:
            cls.account_income = cls.env['account.account'].create({
                'name': 'Product Sales Test',
                'code': '400999',
                'account_type': 'income',
                'company_ids': [Command.link(cls.company.id)],
            })

        cls.account_receivable = cls.env['account.account'].search([
            ('account_type', '=', 'asset_receivable'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.account_receivable:
            cls.account_receivable = cls.env['account.account'].create({
                'name': 'Receivables Test',
                'code': '120999',
                'account_type': 'asset_receivable',
                'company_ids': [Command.link(cls.company.id)],
            })

        group_invoice = cls.env.ref('account.group_account_invoice')
        grp_mgr_xmlid = (
            'double_validation_invoice.'
            'double_validation_invoice_group_manager'
        )
        grp_fin_mgr_xmlid = (
            'double_validation_invoice.'
            'double_validation_invoice_group_finance_manager'
        )
        group_manager = cls.env.ref(grp_mgr_xmlid)
        group_finance_manager = cls.env.ref(grp_fin_mgr_xmlid)

        cls.user_normal = cls.env['res.users'].create({
            'name': 'Invoice Normal User',
            'login': 'inv_normal_user',
            'email': 'inv_normal@example.com',
            'group_ids': [Command.set([
                cls.env.ref('base.group_user').id,
                group_invoice.id,
            ])],
        })

        cls.user_manager = cls.env['res.users'].create({
            'name': 'Invoice Validation Manager',
            'login': 'inv_manager_user',
            'email': 'inv_manager@example.com',
            'group_ids': [Command.set([
                cls.env.ref('base.group_user').id,
                group_invoice.id,
                group_manager.id,
            ])],
        })

        cls.user_finance_manager = cls.env['res.users'].create({
            'name': 'Invoice Finance Manager',
            'login': 'inv_finance_manager_user',
            'email': 'inv_fin_manager@example.com',
            'group_ids': [Command.set([
                cls.env.ref('base.group_user').id,
                group_invoice.id,
                group_finance_manager.id,
            ])],
        })

    def setUp(self):
        super().setUp()
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_bool('double_validation_invoice.double_validation', True)
        icp.set_float('double_validation_invoice.first_valid_limit', 1000.0)
        icp.set_float('double_validation_invoice.second_valid_limit', 2000.0)

    def _create_invoice(self, amount):
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.journal_sale.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': [
                Command.create({
                    'name': 'Product Test',
                    'quantity': 1.0,
                    'price_unit': amount,
                    'account_id': self.account_income.id,
                    'tax_ids': [Command.clear()],
                }),
            ],
        })

    def _create_misc_entry(self, amount):
        return self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.journal_misc.id,
            'date': fields.Date.context_today(self),
            'line_ids': [
                Command.create({
                    'name': 'Debit line',
                    'account_id': self.account_receivable.id,
                    'debit': amount,
                    'credit': 0.0,
                }),
                Command.create({
                    'name': 'Credit line',
                    'account_id': self.account_income.id,
                    'debit': 0.0,
                    'credit': amount,
                }),
            ],
        })

    def test_01_invoice_below_first_limit_posts_directly(self):
        """Invoice with amount <= first_valid_limit posts directly."""
        inv = self._create_invoice(500.0)
        self.assertEqual(inv.state, 'draft')
        inv.action_post()
        self.assertEqual(inv.state, 'posted')

    def test_02_invoice_above_first_below_second_limit(self):
        """Invoice between limits requires only first approval."""
        inv = self._create_invoice(1500.0)
        inv.action_post()
        self.assertEqual(inv.state, 'first_approval')

        # Approve by Manager -> moves directly to posted since <= second limit
        inv.with_user(self.user_manager).action_first_approval()
        self.assertEqual(inv.state, 'posted')

    def test_03_invoice_above_second_limit_two_level_approval(self):
        """Invoice > second limit requires two approval stages."""
        inv = self._create_invoice(2500.0)
        inv.action_post()
        self.assertEqual(inv.state, 'first_approval')

        # Manager approves first level
        inv.with_user(self.user_manager).action_first_approval()
        self.assertEqual(inv.state, 'second_approval')

        # Finance Manager approves second level
        inv.with_user(self.user_finance_manager).action_second_approval()
        self.assertEqual(inv.state, 'posted')

    def test_04_batch_and_non_invoice_posting(self):
        """Multi-record posting works and non-invoices bypass approval."""
        entry = self._create_misc_entry(10000.0)
        inv_low = self._create_invoice(400.0)
        inv_high = self._create_invoice(1500.0)

        moves = entry + inv_low + inv_high
        moves.action_post()

        self.assertEqual(entry.state, 'posted')
        self.assertEqual(inv_low.state, 'posted')
        self.assertEqual(inv_high.state, 'first_approval')

    def test_05_rejection_and_reset_to_draft(self):
        """Approval states can be rejected or reset to draft by managers."""
        inv = self._create_invoice(2500.0)
        inv.action_post()
        self.assertEqual(inv.state, 'first_approval')

        # Normal user does NOT see reset to draft button on first_approval
        inv.invalidate_recordset(['show_reset_to_draft_button'])
        self.assertFalse(
            inv.with_user(self.user_normal).show_reset_to_draft_button
        )
        # Manager sees reset to draft button on first_approval
        inv.invalidate_recordset(['show_reset_to_draft_button'])
        self.assertTrue(
            inv.with_user(self.user_manager).show_reset_to_draft_button
        )

        # Manager rejects first approval -> reset to draft
        inv.with_user(self.user_manager).action_reject()
        self.assertEqual(inv.state, 'draft')

        # Post again and advance to second_approval
        inv.action_post()
        inv.with_user(self.user_manager).action_first_approval()
        self.assertEqual(inv.state, 'second_approval')

        # Manager (not Finance Manager) does not see reset on second_approval
        inv.invalidate_recordset(['show_reset_to_draft_button'])
        self.assertFalse(
            inv.with_user(self.user_manager).show_reset_to_draft_button
        )
        # Finance Manager sees reset on second_approval
        inv.invalidate_recordset(['show_reset_to_draft_button'])
        self.assertTrue(
            inv.with_user(self.user_finance_manager).show_reset_to_draft_button
        )

        # Finance Manager rejects second approval -> reset to draft
        inv.with_user(self.user_finance_manager).action_reject()
        self.assertEqual(inv.state, 'draft')

        # Test authorized button_draft directly from approval states
        inv.action_post()
        self.assertEqual(inv.state, 'first_approval')
        inv.with_user(self.user_manager).button_draft()
        self.assertEqual(inv.state, 'draft')

    def test_06_server_side_security_checks(self):
        """Only authorized groups can approve, post, or reset moves."""
        inv = self._create_invoice(2500.0)
        inv.action_post()
        self.assertEqual(inv.state, 'first_approval')

        # Normal user cannot post directly from first_approval
        with self.assertRaises(UserError):
            inv.with_user(self.user_normal).action_post()

        # Normal user cannot approve first stage
        with self.assertRaises(UserError):
            inv.with_user(self.user_normal).action_first_approval()

        # Normal user cannot reject or reset to draft from first_approval
        with self.assertRaises(UserError):
            inv.with_user(self.user_normal).action_reject()
        with self.assertRaises(UserError):
            inv.with_user(self.user_normal).button_draft()

        # Manager approves first stage
        inv.with_user(self.user_manager).action_first_approval()
        self.assertEqual(inv.state, 'second_approval')

        # Normal user or Manager cannot post directly from second_approval
        with self.assertRaises(UserError):
            inv.with_user(self.user_normal).action_post()
        with self.assertRaises(UserError):
            inv.with_user(self.user_manager).action_post()

        # Manager (without finance manager group) cannot approve second stage
        with self.assertRaises(UserError):
            inv.with_user(self.user_manager).action_second_approval()

        # Manager (without finance manager group) cannot reset second_approval
        with self.assertRaises(UserError):
            inv.with_user(self.user_manager).action_reject()
        with self.assertRaises(UserError):
            inv.with_user(self.user_manager).button_draft()

        # Finance Manager can approve second stage
        inv.with_user(self.user_finance_manager).action_second_approval()
        self.assertEqual(inv.state, 'posted')

    def test_07_double_validation_disabled(self):
        """When disabled, invoices post directly without approval."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'double_validation_invoice.double_validation', False
        )
        inv = self._create_invoice(5000.0)
        inv.action_post()
        self.assertEqual(inv.state, 'posted')
