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
from odoo.tests import common, tagged
from odoo import fields
from datetime import timedelta


@tagged('post_install', '-at_install')
class TestAnomalyEngine(common.TransactionCase):
    """Test suite for models/anomaly_engine.py methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls.env['account.anomaly.engine']
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Vendor AnomalyEngine',
        })
        cls.journal = cls.env['account.journal'].search([
            ('company_id', '=', cls.company.id),
            ('type', '=', 'general')
        ], limit=1)
        cls.expense_account = cls.env['account.account'].search([
            ('company_ids', 'in', [cls.company.id]),
            ('account_type', '=', 'expense')
        ], limit=1)
        cls.cash_account = cls.env['account.account'].search([
            ('company_ids', 'in', [cls.company.id]),
            ('account_type', '=', 'asset_cash')
        ], limit=1)

    def test_cron_run_auto_scan(self):
        """Test _cron_run_auto_scan method."""
        self.company.anomaly_auto_scan_enabled = True
        self.engine._cron_run_auto_scan()

        self.company.anomaly_auto_scan_enabled = False
        self.engine._cron_run_auto_scan()

    def test_run_full_scan(self):
        """Test run_full_scan method."""
        summary = self.engine.run_full_scan()
        self.assertIn('total_alerts', summary)
        self.assertIn('new_alerts', summary)
        self.assertIn('scan_date', summary)

    def test_detect_custom_rules(self):
        """Test _detect_custom_rules method for keyword and amount threshold rules."""
        rule_amount = self.env['account.anomaly.rule'].create({
            'name': 'High Amount Rule',
            'rule_type': 'amount_threshold',
            'min_amount': 5000.0,
            'max_amount': 0.0,
            'score': 80,
            'risk_level': 'high',
            'company_id': self.company.id,
        })
        rule_keyword = self.env['account.anomaly.rule'].create({
            'name': 'Suspicious Keyword Rule',
            'rule_type': 'keyword',
            'keywords': 'suspicious, urgent',
            'score': 90,
            'risk_level': 'high',
            'company_id': self.company.id,
        })

        move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.journal.id,
            'ref': 'suspicious transfer',
            'line_ids': [
                (0, 0, {'account_id': self.expense_account.id, 'debit': 6000.0, 'credit': 0.0}),
                (0, 0, {'account_id': self.cash_account.id, 'debit': 0.0, 'credit': 6000.0}),
            ]
        })

        alerts = self.engine._detect_custom_rules(move, [self.company.id])
        self.assertTrue(len(alerts) >= 1)

    def test_detect_amount_outliers(self):
        """Test _detect_amount_outliers method with statistical outlier."""
        moves = self.env['account.move']
        # Create normal entries
        for amount in [100.0, 105.0, 95.0, 102.0, 98.0]:
            m = self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': self.journal.id,
                'line_ids': [
                    (0, 0, {'account_id': self.expense_account.id, 'debit': amount, 'credit': 0.0}),
                    (0, 0, {'account_id': self.cash_account.id, 'debit': 0.0, 'credit': amount}),
                ]
            })
            moves |= m

        # Create extreme outlier
        outlier = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {'account_id': self.expense_account.id, 'debit': 10000.0, 'credit': 0.0}),
                (0, 0, {'account_id': self.cash_account.id, 'debit': 0.0, 'credit': 10000.0}),
            ]
        })
        moves |= outlier

        self.company.anomaly_zscore_threshold = 2.0
        alerts = self.engine._detect_amount_outliers(moves)
        self.assertTrue(any(a.move_id == outlier for a in alerts))

    def test_detect_duplicate_bills(self):
        """Test _detect_duplicate_bills method."""
        bill_journal = self.env['account.journal'].search([
            ('company_id', '=', self.company.id),
            ('type', '=', 'purchase')
        ], limit=1)

        if not bill_journal:
            return

        bill1 = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'journal_id': bill_journal.id,
            'partner_id': self.partner.id,
            'ref': 'INV-1001',
            'invoice_date': fields.Date.today(),
            'line_ids': [
                (0, 0, {'account_id': self.expense_account.id, 'price_unit': 500.0, 'quantity': 1}),
            ]
        })

        bill2 = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'journal_id': bill_journal.id,
            'partner_id': self.partner.id,
            'ref': 'INV-1001',
            'invoice_date': fields.Date.today(),
            'line_ids': [
                (0, 0, {'account_id': self.expense_account.id, 'price_unit': 500.0, 'quantity': 1}),
            ]
        })

        moves = bill1 | bill2
        alerts = self.engine._detect_duplicate_bills(
            moves, fields.Date.today() - timedelta(days=5), fields.Date.today(), [self.company.id])
        self.assertTrue(len(alerts) >= 1)

    def test_detect_round_number_bias(self):
        """Test _detect_round_number_bias method."""
        move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {'account_id': self.expense_account.id, 'debit': 5000.0, 'credit': 0.0}),
                (0, 0, {'account_id': self.cash_account.id, 'debit': 0.0, 'credit': 5000.0}),
            ]
        })
        self.company.anomaly_round_number_threshold = 1000.0
        alerts = self.engine._detect_round_number_bias(move)
        self.assertTrue(any(a.move_id == move for a in alerts))

    def test_detect_transaction_velocity(self):
        """Test _detect_transaction_velocity method."""
        self.company.anomaly_velocity_window_days = 3
        self.company.anomaly_velocity_max_count = 3

        moves = self.env['account.move']
        today = fields.Date.today()
        for i in range(4):
            m = self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': self.journal.id,
                'partner_id': self.partner.id,
                'date': today,
                'line_ids': [
                    (0, 0, {'account_id': self.expense_account.id, 'debit': 100.0, 'credit': 0.0}),
                    (0, 0, {'account_id': self.cash_account.id, 'debit': 0.0, 'credit': 100.0}),
                ]
            })
            moves |= m

        alerts = self.engine._detect_transaction_velocity(moves, today - timedelta(days=5), today)
        self.assertTrue(len(alerts) >= 1)

    def test_detect_unusual_timing(self):
        """Test _detect_unusual_timing method on weekend dates."""
        # Find next Saturday date
        today = fields.Date.today()
        saturday = today + timedelta(days=(5 - today.weekday()) % 7)

        move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.journal.id,
            'date': saturday,
            'line_ids': [
                (0, 0, {'account_id': self.expense_account.id, 'debit': 200.0, 'credit': 0.0}),
                (0, 0, {'account_id': self.cash_account.id, 'debit': 0.0, 'credit': 200.0}),
            ]
        })

        alerts = self.engine._detect_unusual_timing(move)
        self.assertTrue(any(a.move_id == move for a in alerts))

    def test_detect_spending_pattern_deviation(self):
        """Test _detect_spending_pattern_deviation method."""
        moves = self.env['account.move']
        alerts = self.engine._detect_spending_pattern_deviation(moves, [self.company.id])
        self.assertIsInstance(alerts, list)

    def test_detect_benfords_law_violation(self):
        """Test _detect_benfords_law_violation method."""
        moves = self.env['account.move']
        alerts = self.engine._detect_benfords_law_violation(moves)
        self.assertIsInstance(alerts, list)

    def test_detect_unusual_account_combinations(self):
        """Test _detect_unusual_account_combinations method."""
        equity_account = self.env['account.account'].search([
            ('company_ids', 'in', [self.company.id]),
            ('account_type', '=', 'equity')
        ], limit=1)

        if equity_account:
            move = self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': self.journal.id,
                'line_ids': [
                    (0, 0, {'account_id': self.cash_account.id, 'debit': 1000.0, 'credit': 0.0}),
                    (0, 0, {'account_id': equity_account.id, 'debit': 0.0, 'credit': 1000.0}),
                ]
            })
            alerts = self.engine._detect_unusual_account_combinations(move)
            self.assertTrue(any(a.move_id == move for a in alerts))

    def test_detect_vendor_concentration(self):
        """Test _detect_vendor_concentration method."""
        moves = self.env['account.move']
        alerts = self.engine._detect_vendor_concentration(moves, fields.Date.today() - timedelta(days=30), fields.Date.today())
        self.assertIsInstance(alerts, list)

    def test_helpers(self):
        """Test helper functions _get_config, _find_existing_alert, _create_alert, _format_currency."""
        config = self.engine._get_config()
        self.assertEqual(config, self.company)

        move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.journal.id,
        })
        alert = self.engine._create_alert(
            move=move,
            alert_type='round_number',
            risk_level='low',
            title='Helper Test Alert',
            description='Test description',
            score=30
        )
        self.assertIsNotNone(alert)

        found = self.engine._find_existing_alert(move, 'round_number')
        self.assertEqual(found, alert)

        formatted = self.engine._format_currency(1234.56, self.company.currency_id)
        self.assertIn('1,234.56', formatted)
