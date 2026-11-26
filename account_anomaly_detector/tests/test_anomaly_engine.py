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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import timedelta
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestAnomalyEngine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.engine = cls.env['account.anomaly.engine']

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Engine Partner',
        })

        cls.journal = cls.env['account.journal'].search([
            ('company_id', '=', cls.company.id),
            ('type', '=', 'purchase')
        ], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Vendor Bills Test',
                'code': 'VBT',
                'type': 'purchase',
                'company_id': cls.company.id,
            })

        cls.account_expense = cls.env['account.account'].search([
            ('company_id', '=', cls.company.id),
            ('account_type', '=', 'expense')
        ], limit=1)

        cls.account_payable = cls.env['account.account'].search([
            ('company_id', '=', cls.company.id),
            ('account_type', '=', 'liability_payable')
        ], limit=1)

        cls.account_equity = cls.env['account.account'].search([
            ('company_id', '=', cls.company.id),
            ('account_type', '=', 'equity')
        ], limit=1)

        cls.account_cash = cls.env['account.account'].search([
            ('company_id', '=', cls.company.id),
            ('account_type', '=', 'asset_cash')
        ], limit=1)

    def test_01_detect_duplicate_bills(self):
        """Test duplicate vendor bill detection algorithm."""
        today = fields.Date.today()
        bill1 = self.env['account.move'].create({
            'company_id': self.company.id,
            'partner_id': self.partner.id,
            'move_type': 'in_invoice',
            'invoice_date': today,
            'date': today,
            'ref': 'INV/2026/001',
            'invoice_line_ids': [
                (0, 0, {'name': 'Item', 'account_id': self.account_expense.id, 'price_unit': 1200.0, 'quantity': 1.0}),
            ]
        })
        bill2 = self.env['account.move'].create({
            'company_id': self.company.id,
            'partner_id': self.partner.id,
            'move_type': 'in_invoice',
            'invoice_date': today,
            'date': today,
            'ref': 'INV/2026/001',
            'invoice_line_ids': [
                (0, 0, {'name': 'Item Dup', 'account_id': self.account_expense.id, 'price_unit': 1200.0, 'quantity': 1.0}),
            ]
        })

        moves = bill1 | bill2
        alerts = self.engine._detect_duplicate_bills(moves, today - timedelta(days=5), today, [self.company.id])
        self.assertTrue(len(alerts) > 0)
        self.assertTrue(any(a.alert_type == 'duplicate_vendor_bill' for a in alerts))

    def test_02_detect_round_number_bias(self):
        """Test round number transaction detection."""
        move = self.env['account.move'].create({
            'company_id': self.company.id,
            'partner_id': self.partner.id,
            'move_type': 'entry',
            'date': fields.Date.today(),
            'line_ids': [
                (0, 0, {'name': 'Round', 'account_id': self.account_expense.id, 'debit': 5000.0, 'credit': 0.0}),
                (0, 0, {'name': 'Round Pay', 'account_id': self.account_payable.id, 'debit': 0.0, 'credit': 5000.0}),
            ]
        })
        alerts = self.engine._detect_round_number_bias(move)
        self.assertTrue(len(alerts) > 0)
        self.assertEqual(alerts[0].alert_type, 'round_number')

    def test_03_detect_unusual_timing(self):
        """Test weekend transaction detection."""
        today = fields.Date.today()
        saturday = today + timedelta(days=(5 - today.weekday()) % 7)

        move = self.env['account.move'].create({
            'company_id': self.company.id,
            'partner_id': self.partner.id,
            'move_type': 'entry',
            'date': saturday,
            'line_ids': [
                (0, 0, {'name': 'W', 'account_id': self.account_expense.id, 'debit': 100.0, 'credit': 0.0}),
                (0, 0, {'name': 'W2', 'account_id': self.account_payable.id, 'debit': 0.0, 'credit': 100.0}),
            ]
        })
        alerts = self.engine._detect_unusual_timing(move)
        self.assertTrue(len(alerts) > 0)
        self.assertEqual(alerts[0].alert_type, 'unusual_timing')

    def test_04_detect_unusual_account_combinations(self):
        """Test unusual debit/credit account type combinations (asset_cash -> equity)."""
        move = self.env['account.move'].create({
            'company_id': self.company.id,
            'move_type': 'entry',
            'date': fields.Date.today(),
            'line_ids': [
                (0, 0, {'name': 'Cash', 'account_id': self.account_cash.id, 'debit': 1000.0, 'credit': 0.0}),
                (0, 0, {'name': 'Equity', 'account_id': self.account_equity.id, 'debit': 0.0, 'credit': 1000.0}),
            ]
        })
        alerts = self.engine._detect_unusual_account_combinations(move)
        self.assertTrue(len(alerts) > 0)
        self.assertEqual(alerts[0].alert_type, 'unusual_account_combo')

    def test_05_detect_custom_rules(self):
        """Test user-defined custom rule evaluation."""
        rule = self.env['account.anomaly.rule'].create({
            'name': 'Keyword Rule',
            'rule_type': 'keyword',
            'keywords': 'cash, urgent',
            'score': 70,
            'company_id': self.company.id,
        })
        move = self.env['account.move'].create({
            'company_id': self.company.id,
            'move_type': 'entry',
            'ref': 'URGENT cash payment',
            'date': fields.Date.today(),
            'line_ids': [
                (0, 0, {'name': 'D', 'account_id': self.account_expense.id, 'debit': 200.0, 'credit': 0.0}),
                (0, 0, {'name': 'C', 'account_id': self.account_payable.id, 'debit': 0.0, 'credit': 200.0}),
            ]
        })
        alerts = self.engine._detect_custom_rules(move, [self.company.id])
        self.assertTrue(len(alerts) > 0)
        self.assertEqual(alerts[0].alert_type, 'manual')
        self.assertEqual(alerts[0].rule_id, rule)

    def test_06_run_full_scan_and_cron(self):
        """Test master run_full_scan and cron wrapper."""
        summary = self.engine.run_full_scan(
            date_from=fields.Date.today() - timedelta(days=10),
            date_to=fields.Date.today(),
            company_ids=[self.company.id]
        )
        self.assertIn('total_alerts', summary)
        self.assertIn('new_alerts', summary)

        # Test with algorithm toggles and include_draft
        summary_toggles = self.engine.run_full_scan(
            date_from=fields.Date.today() - timedelta(days=10),
            date_to=fields.Date.today(),
            company_ids=[self.company.id],
            include_draft=True,
            algorithms={'amount_outliers': False, 'duplicates': False}
        )
        self.assertIn('total_alerts', summary_toggles)

        self.company.anomaly_auto_scan_enabled = True
        self.company.anomaly_scan_frequency = 'weekly'
        self.engine._cron_run_auto_scan()
        self.company.anomaly_scan_frequency = 'hourly'
        self.engine._cron_run_auto_scan()
