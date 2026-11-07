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
from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosSession(TransactionCase):
    """Test cases for the pos.session model and its functions in pos_analytic_tag."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Create analytic plan (without company_id) and analytic account
        cls.analytic_plan = cls.env['account.analytic.plan'].create({
            'name': 'POS Test Analytic Plan',
        })
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'POS Test Analytic Account',
            'plan_id': cls.analytic_plan.id,
            'company_id': cls.company.id,
        })

        # Create account journal for POS sales
        cls.pos_sale_journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.pos_sale_journal:
            cls.pos_sale_journal = cls.env['account.journal'].create({
                'name': 'POS Sale Journal',
                'type': 'sale',
                'code': 'TPOSS',
                'company_id': cls.company.id,
            })

        # Create bank journal for payment method
        cls.bank_journal = cls.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.bank_journal:
            cls.bank_journal = cls.env['account.journal'].create({
                'name': 'POS Bank Journal',
                'type': 'bank',
                'code': 'TPOSB',
                'company_id': cls.company.id,
            })

        # Create test receivable and income accounts for journal entries
        cls.account_receivable = cls.env['account.account'].search([
            ('account_type', '=', 'asset_receivable'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.account_receivable:
            cls.account_receivable = cls.env['account.account'].create({
                'name': 'Test Receivable Account',
                'code': 'TREC1',
                'account_type': 'asset_receivable',
                'company_ids': [Command.link(cls.company.id)],
            })

        cls.account_income = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.account_income:
            cls.account_income = cls.env['account.account'].create({
                'name': 'Test Income Account',
                'code': 'TINC1',
                'account_type': 'income',
                'company_ids': [Command.link(cls.company.id)],
            })

        # Create payment method with required type and journal
        cls.payment_method = cls.env['pos.payment.method'].create({
            'name': 'Test Bank Payment Method',
            'type': 'bank',
            'journal_id': cls.bank_journal.id,
            'receivable_account_id': cls.account_receivable.id,
            'company_id': cls.company.id,
        })

        # Create POS config with analytic account
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Config with Analytic',
            'journal_id': cls.pos_sale_journal.id,
            'analytic_account_id': cls.analytic_account.id,
            'payment_method_ids': [Command.link(cls.payment_method.id)],
        })

        # Create POS config without analytic account
        cls.pos_config_no_analytic = cls.env['pos.config'].create({
            'name': 'Test POS Config without Analytic',
            'journal_id': cls.pos_sale_journal.id,
            'analytic_account_id': False,
            'payment_method_ids': [Command.link(cls.payment_method.id)],
        })

        # Create POS sessions
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
        })
        cls.pos_session_no_analytic = cls.env['pos.session'].create({
            'config_id': cls.pos_config_no_analytic.id,
        })

    def test__load_pos_data_fields(self):
        """Test _load_pos_data_fields method to ensure pos_analytic_account_id is loaded."""
        fields = self.env['pos.session']._load_pos_data_fields(self.pos_config.id)
        self.assertIsInstance(fields, list, "_load_pos_data_fields must return a list of field names")
        self.assertIn(
            'pos_analytic_account_id',
            fields,
            "pos_analytic_account_id should be in the returned pos.session fields list"
        )

        # Verify calling with config recordset as well
        fields_record = self.env['pos.session']._load_pos_data_fields(self.pos_config)
        self.assertIn(
            'pos_analytic_account_id',
            fields_record,
            "pos_analytic_account_id should be returned when passing a pos.config record"
        )

        # Verify idempotency (no duplicates if field is already present in fields list)
        count = fields.count('pos_analytic_account_id')
        self.assertEqual(count, 1, "pos_analytic_account_id should not be duplicated in the fields list")

    def test_load_pos_data_fields(self):
        """Alias for test__load_pos_data_fields without leading underscore."""
        self.test__load_pos_data_fields()

    def test__create_session_account_move(self):
        """Test _create_session_account_move with and without analytic account."""
        # 1. Test case: POS Config has an analytic account configured
        move_with_analytic = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.pos_sale_journal.id,
            'pos_session_sales_id': self.pos_session.id,
            'line_ids': [
                Command.create({
                    'account_id': self.account_income.id,
                    'name': 'Test sale line',
                    'credit': 100.0,
                }),
                Command.create({
                    'account_id': self.account_receivable.id,
                    'name': 'Test receivable line',
                    'debit': 100.0,
                }),
            ],
        })

        empty_orders = self.env['pos.order']
        res = self.pos_session._create_session_account_move(empty_orders)

        self.assertEqual(
            self.pos_session.pos_analytic_account_id,
            self.analytic_account,
            "Session pos_analytic_account_id should be set from config_id.analytic_account_id"
        )

        expected_distribution = {str(self.analytic_account.id): 100}
        for line in move_with_analytic.line_ids:
            self.assertEqual(
                line.analytic_distribution,
                expected_distribution,
                "Move lines should have analytic_distribution set to 100% for the analytic account"
            )

        # Verify related fields on pos.order and pos.payment
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'company_id': self.company.id,
            'amount_tax': 0.0,
            'amount_total': 100.0,
            'amount_paid': 100.0,
            'amount_return': 0.0,
            'partner_id': self.env.user.partner_id.id,
        })
        self.assertEqual(
            order.pos_analytic_account_id,
            self.analytic_account,
            "pos.order should get pos_analytic_account_id related from session"
        )

        payment = self.env['pos.payment'].create({
            'pos_order_id': order.id,
            'amount': 100.0,
            'payment_method_id': self.payment_method.id,
        })
        self.assertEqual(
            payment.pos_analytic_account_id,
            self.analytic_account,
            "pos.payment should get pos_analytic_account_id related from session"
        )

        # 2. Test case: POS Config has NO analytic account configured
        move_without_analytic = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.pos_sale_journal.id,
            'pos_session_sales_id': self.pos_session_no_analytic.id,
            'line_ids': [
                Command.create({
                    'account_id': self.account_income.id,
                    'name': 'Test sale line no analytic',
                    'credit': 50.0,
                    'analytic_distribution': {str(self.analytic_account.id): 100},
                }),
                Command.create({
                    'account_id': self.account_receivable.id,
                    'name': 'Test receivable line no analytic',
                    'debit': 50.0,
                }),
            ],
        })

        res_no_analytic = self.pos_session_no_analytic._create_session_account_move(empty_orders)

        self.assertFalse(
            self.pos_session_no_analytic.pos_analytic_account_id,
            "Session pos_analytic_account_id should be False when config has no analytic account"
        )

        for line in move_without_analytic.line_ids:
            self.assertFalse(
                line.analytic_distribution,
                "Move lines should have empty analytic_distribution when no analytic account is configured"
            )

    def test_create_session_account_move(self):
        """Alias for test__create_session_account_move without leading underscore."""
        self.test__create_session_account_move()
