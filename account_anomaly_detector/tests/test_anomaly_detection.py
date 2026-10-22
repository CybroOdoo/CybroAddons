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
"""Unit and integration test suite for AI Anomaly Detection module."""

from datetime import date, timedelta
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install')
class TestAnomalyDetection(TransactionCase):
    """Test suite exercising all algorithms, hooks, wizard, and workflows."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.anomaly_scan_on_post = False
        cls.env['res.company'].search([]).write({
            'anomaly_auto_scan_enabled': False,
        })
        cls.engine = cls.env['account.anomaly.engine']

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Audit Partner',
        })

        # Standard general journal
        cls.journal_misc = cls.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.journal_misc:
            cls.journal_misc = cls.env['account.journal'].create({
                'name': 'Audit Misc Journal',
                'code': 'AMISC',
                'type': 'general',
                'company_id': cls.company.id,
            })

        # Purchase journal
        cls.journal_purchase = cls.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.journal_purchase:
            cls.journal_purchase = cls.env['account.journal'].create({
                'name': 'Audit Purchase Journal',
                'code': 'APUR',
                'type': 'purchase',
                'company_id': cls.company.id,
            })

        # Accounts for testing
        cls.account_expense = cls.env['account.account'].search([
            ('account_type', '=', 'expense'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.account_expense:
            cls.account_expense = cls.env['account.account'].create({
                'name': 'Audit Office Expense',
                'code': '600999',
                'account_type': 'expense',
                'company_ids': [(4, cls.company.id)],
            })

        cls.account_cash = cls.env['account.account'].search([
            ('account_type', '=', 'asset_cash'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.account_cash:
            cls.account_cash = cls.env['account.account'].create({
                'name': 'Audit Main Cash',
                'code': '101999',
                'account_type': 'asset_cash',
                'company_ids': [(4, cls.company.id)],
            })

        cls.account_equity = cls.env['account.account'].search([
            ('account_type', '=', 'equity'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.account_equity:
            cls.account_equity = cls.env['account.account'].create({
                'name': 'Audit Equity',
                'code': '300999',
                'account_type': 'equity',
                'company_ids': [(4, cls.company.id)],
            })

        cls.account_payable = cls.env['account.account'].search([
            ('account_type', '=', 'liability_payable'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.account_payable:
            cls.account_payable = cls.env['account.account'].create({
                'name': 'Audit Payables',
                'code': '201999',
                'account_type': 'liability_payable',
                'company_ids': [(4, cls.company.id)],
            })

    def _create_misc_entry(self, debit_acc, credit_acc, amount, entry_date):
        """Helper to create and post a balanced journal entry."""
        move = self.env['account.move'].create({
            'journal_id': self.journal_misc.id,
            'date': entry_date,
            'move_type': 'entry',
            'line_ids': [
                (0, 0, {
                    'account_id': debit_acc.id,
                    'name': 'Debit Line',
                    'debit': amount,
                    'credit': 0.0,
                    'partner_id': self.partner.id,
                }),
                (0, 0, {
                    'account_id': credit_acc.id,
                    'name': 'Credit Line',
                    'debit': 0.0,
                    'credit': amount,
                    'partner_id': self.partner.id,
                }),
            ],
        })
        move.action_post()
        return move

    def test_01_amount_outlier_detection(self):
        """Test Z-Score outlier detection with normal amounts vs extreme."""
        today = date.today()
        # Create 5 baseline posted transactions around 100
        for i in range(5):
            self._create_misc_entry(
                self.account_expense, self.account_cash,
                100.0 + (i * 2), today - timedelta(days=10 - i)
            )

        # Create 1 extreme outlier transaction of 250,000
        outlier_move = self._create_misc_entry(
            self.account_expense, self.account_cash,
            250000.0, today
        )

        alerts = self.engine._detect_amount_outliers(outlier_move)
        self.assertTrue(alerts, "Amount outlier should have generated alerts")
        self.assertEqual(alerts[0].alert_type, 'amount_outlier')
        self.assertIn(alerts[0].risk_level, ['high', 'critical'])
        self.assertGreaterEqual(alerts[0].anomaly_score, 50)

    def test_02_duplicate_vendor_bill(self):
        """Test duplicate bill detection with identical amounts."""
        today = date.today()
        bill1 = self.env['account.move'].create({
            'journal_id': self.journal_purchase.id,
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_date': today,
            'date': today,
            'ref': 'INV-TEST-001',
            'invoice_line_ids': [(0, 0, {
                'name': 'Consulting Service A',
                'account_id': self.account_expense.id,
                'price_unit': 4500.0,
                'quantity': 1,
            })],
        })
        bill1.action_post()

        bill2 = self.env['account.move'].create({
            'journal_id': self.journal_purchase.id,
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_date': today,
            'date': today,
            'ref': 'INV-TEST-001-DUP',
            'invoice_line_ids': [(0, 0, {
                'name': 'Consulting Service A',
                'account_id': self.account_expense.id,
                'price_unit': 4500.0,
                'quantity': 1,
            })],
        })
        bill2.action_post()

        moves = bill1 | bill2
        alerts = self.engine._detect_duplicate_bills(
            moves, today - timedelta(days=5), today, [self.company.id]
        )
        self.assertTrue(alerts, "Duplicate bills should generate alert")
        dup_alerts = [
            a for a in alerts if a.alert_type == 'duplicate_vendor_bill'
        ]
        self.assertTrue(dup_alerts)
        self.assertEqual(dup_alerts[0].risk_level, 'critical')

    def test_03_round_number_bias(self):
        """Test round number bias detection for large round transactions."""
        today = date.today()
        move = self._create_misc_entry(
            self.account_expense, self.account_cash,
            50000.0, today
        )
        alerts = self.engine._detect_round_number_bias(move)
        self.assertTrue(alerts)
        self.assertEqual(alerts[0].alert_type, 'round_number')

    def test_04_unusual_timing(self):
        """Test detection of transactions recorded on weekends."""
        # 2026-10-24 is a Saturday (weekday == 5)
        saturday_date = date(2026, 10, 24)
        move = self._create_misc_entry(
            self.account_expense, self.account_cash,
            250.0, saturday_date
        )
        alerts = self.engine._detect_unusual_timing(move)
        self.assertTrue(alerts)
        self.assertEqual(alerts[0].alert_type, 'unusual_timing')
        self.assertIn('Saturday', alerts[0].description)

    def test_05_unusual_account_combination(self):
        """Test high-risk account combination (asset_cash -> equity)."""
        today = date.today()
        move = self._create_misc_entry(
            self.account_cash, self.account_equity,
            12000.0, today
        )
        alerts = self.engine._detect_unusual_account_combinations(move)
        self.assertTrue(alerts)
        self.assertEqual(alerts[0].alert_type, 'unusual_account_combo')

    def test_06_custom_rules(self):
        """Test custom audit rule triggering and hit tracking."""
        rule = self.env['account.anomaly.rule'].create({
            'name': 'High Value Audit Threshold',
            'rule_type': 'amount_threshold',
            'min_amount': 20000.0,
            'score': 85,
            'company_id': self.company.id,
        })
        self.assertEqual(rule.risk_level, 'high')

        today = date.today()
        move = self._create_misc_entry(
            self.account_expense, self.account_cash,
            30000.0, today
        )

        alerts = self.engine._detect_custom_rules(move, [self.company.id])
        self.assertTrue(alerts)
        self.assertEqual(alerts[0].alert_type, 'manual')
        self.assertEqual(alerts[0].anomaly_score, 85)
        self.assertEqual(rule.hits_count, 1)

    def test_07_scan_on_post_with_historical_baseline(self):
        """Test that action_post runs anomaly checks with baseline."""
        self.company.anomaly_scan_on_post = True
        today = date.today()

        # Build baseline of 5 transactions
        for i in range(5):
            self._create_misc_entry(
                self.account_expense, self.account_cash,
                80.0 + i, today - timedelta(days=15 - i)
            )

        # Post an extreme outlier directly
        outlier = self.env['account.move'].create({
            'journal_id': self.journal_misc.id,
            'date': today,
            'move_type': 'entry',
            'line_ids': [
                (0, 0, {
                    'account_id': self.account_expense.id,
                    'name': 'Outlier Line',
                    'debit': 999999.0,
                    'credit': 0.0,
                    'partner_id': self.partner.id,
                }),
                (0, 0, {
                    'account_id': self.account_cash.id,
                    'name': 'Outlier Line 2',
                    'debit': 0.0,
                    'credit': 999999.0,
                    'partner_id': self.partner.id,
                }),
            ],
        })
        outlier.action_post()

        # Check that outlier alerts were created automatically on posting
        alerts = outlier.anomaly_alert_ids
        self.assertTrue(alerts, "Scan on post should create alert on outlier")
        self.assertGreater(outlier.anomaly_alert_count, 0)
        self.assertIn(outlier.anomaly_risk_level, ['high', 'critical'])

    def test_08_wizard_algorithm_toggles(self):
        """Test wizard execution and respect for algorithm toggles."""
        today = date.today()
        wizard = self.env['account.anomaly.scan.wizard'].create({
            'date_from': today - timedelta(days=7),
            'date_to': today,
            'scan_all': False,
            'scan_duplicates': False,
            'scan_amount_outliers': True,
        })
        action = wizard.action_run_scan()
        self.assertEqual(action.get('res_model'), 'account.anomaly.alert')
        self.assertIn('anomaly_scan_summary', action.get('context', {}))

    def test_09_account_and_partner_exclusions(self):
        """Verify that excluded accounts and partners never trigger alerts."""
        today = date.today()

        # Exclude accounts involved in transaction
        self.company.anomaly_excluded_account_ids = [
            (4, self.account_expense.id),
            (4, self.account_cash.id),
        ]

        move_excluded_acc = self._create_misc_entry(
            self.account_expense, self.account_cash,
            750000.0, today
        )
        alerts_acc = self.engine._detect_amount_outliers(move_excluded_acc)
        self.assertFalse(
            alerts_acc, "Excluded accounts must not trigger outlier alerts"
        )

        # Exclude partner
        self.company.anomaly_excluded_partner_ids = [(4, self.partner.id)]
        bill1 = self.env['account.move'].create({
            'journal_id': self.journal_purchase.id,
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_date': today,
            'date': today,
            'invoice_line_ids': [(0, 0, {
                'name': 'Consulting X',
                'account_id': self.account_expense.id,
                'price_unit': 8888.0,
                'quantity': 1,
            })],
        })
        bill1.action_post()

        bill2 = self.env['account.move'].create({
            'journal_id': self.journal_purchase.id,
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_date': today,
            'date': today,
            'invoice_line_ids': [(0, 0, {
                'name': 'Consulting X',
                'account_id': self.account_expense.id,
                'price_unit': 8888.0,
                'quantity': 1,
            })],
        })
        bill2.action_post()

        dup_alerts = self.engine._detect_duplicate_bills(
            bill1 | bill2, today - timedelta(days=5), today, [self.company.id]
        )
        self.assertFalse(
            dup_alerts, "Excluded partners must not trigger duplicate alerts"
        )

    def test_10_notifications_and_cron_sync(self):
        """Test cron synchronization and notification dispatch."""
        cron = self.env.ref('account_anomaly_detector.cron_anomaly_daily_scan')

        # Test weekly sync
        self.company.write({
            'anomaly_auto_scan_enabled': True,
            'anomaly_scan_frequency': 'weekly',
        })
        self.assertTrue(cron.active)
        self.assertEqual(cron.interval_type, 'weeks')

        # Test hourly sync
        self.company.write({
            'anomaly_scan_frequency': 'hourly',
        })
        self.assertEqual(cron.interval_type, 'hours')

        # Test daily sync
        self.company.write({
            'anomaly_scan_frequency': 'daily',
        })
        self.assertEqual(cron.interval_type, 'days')

        # Test notification dispatch
        self.company.write({
            'anomaly_notify_critical': True,
            'anomaly_notify_auditor_group': True,
            'anomaly_notification_user_ids': [(4, self.env.user.id)],
        })
        today = date.today()
        move = self._create_misc_entry(
            self.account_expense, self.account_cash,
            500.0, today
        )
        alert = self.engine._create_alert(
            move=move,
            alert_type='manual',
            risk_level='critical',
            title='Critical Test Alert',
            description='Test notification dispatching',
            score=95,
        )
        self.assertIsNotNone(alert)
        self.assertEqual(alert.risk_level, 'critical')

    def test_11_pdf_report_and_company_filter(self):
        """Test that PDF report values correctly filter by company."""
        today = date.today()
        move = self._create_misc_entry(
            self.account_expense, self.account_cash,
            350.0, today
        )
        alert = self.engine._create_alert(
            move=move,
            alert_type='manual',
            risk_level='high',
            title='Report Verification Alert',
            description='Testing PDF report data structure',
            score=70,
        )

        report_cls = self.env[
            'report.account_anomaly_detector.report_anomaly_alerts_document'
        ]
        values = report_cls._get_report_values(docids=None)
        self.assertIn('docs', values)
        self.assertIn(alert.id, values['docs'].ids)
        self.assertGreaterEqual(values['high_count'], 1)

    def test_12_alert_workflow_actions(self):
        """Test alert state machine transitions and resolution notes."""
        today = date.today()
        move = self._create_misc_entry(
            self.account_expense, self.account_cash,
            120.0, today
        )
        alert = self.engine._create_alert(
            move=move,
            alert_type='round_number',
            risk_level='low',
            title='Workflow Test Alert',
            description='Testing alert action methods',
            score=25,
        )
        self.assertEqual(alert.state, 'open')

        # Investigate
        alert.action_investigate()
        self.assertEqual(alert.state, 'investigating')
        self.assertEqual(alert.assigned_to, self.env.user)

        # Escalate
        alert.action_escalate()
        self.assertEqual(alert.state, 'escalated')

        # Resolve requires resolution note
        with self.assertRaises(UserError):
            alert.action_resolve()

        alert.resolution_note = "Valid business purpose confirmed."
        alert.action_resolve()
        self.assertEqual(alert.state, 'resolved')
        self.assertIsNotNone(alert.resolved_date)

        # Batch resolve
        alert2 = self.engine._create_alert(
            move=move,
            alert_type='manual',
            risk_level='low',
            title='Batch Resolve Test',
            description='Testing batch resolution',
            score=15,
        )
        alert2.action_batch_resolve()
        self.assertEqual(alert2.state, 'resolved')
        self.assertEqual(alert2.resolution_note, 'Batch resolved')

    def test_13_anomaly_score_constraint(self):
        """Test constraint rejecting scores outside 0-100."""
        today = date.today()
        move = self._create_misc_entry(
            self.account_expense, self.account_cash,
            100.0, today
        )
        with self.assertRaises(ValidationError):
            self.env['account.anomaly.alert'].create({
                'title': 'Invalid Score Alert',
                'description': 'Score out of range',
                'alert_type': 'manual',
                'anomaly_score': 150,
                'move_id': move.id,
                'company_id': self.company.id,
            })

    def test_14_velocity_spikes_and_benfords_law(self):
        """Test transaction velocity burst and Benford's law detection."""
        today = date.today()
        self.company.anomaly_velocity_max_count = 3
        self.company.anomaly_velocity_window_days = 5

        moves = self.env['account.move']
        for i in range(4):
            m = self.env['account.move'].create({
                'journal_id': self.journal_purchase.id,
                'move_type': 'in_invoice',
                'partner_id': self.partner.id,
                'invoice_date': today - timedelta(days=i % 2),
                'date': today - timedelta(days=i % 2),
                'invoice_line_ids': [(0, 0, {
                    'name': f'Rapid Bill {i}',
                    'account_id': self.account_expense.id,
                    'price_unit': 100.0 + i,
                    'quantity': 1,
                })],
            })
            m.action_post()
            moves |= m

        velocity_alerts = self.engine._detect_transaction_velocity(
            moves, today - timedelta(days=10), today
        )
        self.assertTrue(velocity_alerts)
        self.assertEqual(velocity_alerts[0].alert_type, 'velocity_spike')

        # Test Benford's Law detection
        self.company.anomaly_enable_benfords_law = True
        partner_fraud = self.env['res.partner'].create({
            'name': 'Benford Test Vendor',
        })
        benford_moves = self.env['account.move']
        # Create 22 invoices all starting with digit 9 to violate Benford
        for i in range(22):
            bm = self.env['account.move'].create({
                'journal_id': self.journal_purchase.id,
                'move_type': 'in_invoice',
                'partner_id': partner_fraud.id,
                'invoice_date': today,
                'date': today,
                'invoice_line_ids': [(0, 0, {
                    'name': f'Benford Item {i}',
                    'account_id': self.account_expense.id,
                    'price_unit': 900.0 + i,
                    'quantity': 1,
                })],
            })
            bm.action_post()
            benford_moves |= bm

        benford_alerts = self.engine._detect_benfords_law_violation(
            benford_moves
        )
        self.assertTrue(benford_alerts)
        self.assertEqual(benford_alerts[0].alert_type, 'benfords_violation')

    def test_15_spending_deviations_and_ref_duplicates(self):
        """Test spending deviation detection and bill reference duplicates."""
        today = date.today()
        # Historical baseline line 60 days ago
        base_move = self.env['account.move'].create({
            'journal_id': self.journal_misc.id,
            'date': today - timedelta(days=60),
            'move_type': 'entry',
            'line_ids': [
                (0, 0, {
                    'account_id': self.account_expense.id,
                    'name': 'Old Expense',
                    'debit': 150.0,
                    'credit': 0.0,
                    'partner_id': self.partner.id,
                }),
                (0, 0, {
                    'account_id': self.account_cash.id,
                    'name': 'Old Cash',
                    'debit': 0.0,
                    'credit': 150.0,
                    'partner_id': self.partner.id,
                }),
            ],
        })
        base_move.action_post()

        # Current move with dramatic spending surge
        current_move = self.env['account.move'].create({
            'journal_id': self.journal_misc.id,
            'date': today - timedelta(days=5),
            'move_type': 'entry',
            'line_ids': [
                (0, 0, {
                    'account_id': self.account_expense.id,
                    'name': 'Huge Surge Expense',
                    'debit': 50000.0,
                    'credit': 0.0,
                    'partner_id': self.partner.id,
                }),
                (0, 0, {
                    'account_id': self.account_cash.id,
                    'name': 'Huge Surge Cash',
                    'debit': 0.0,
                    'credit': 50000.0,
                    'partner_id': self.partner.id,
                }),
            ],
        })
        current_move.action_post()

        dev_alerts = self.engine._detect_spending_pattern_deviation(
            base_move | current_move, [self.company.id]
        )
        self.assertTrue(dev_alerts)
        self.assertEqual(dev_alerts[0].alert_type, 'spending_deviation')

        # Test duplicate vendor bill reference
        dup1 = self.env['account.move'].create({
            'journal_id': self.journal_purchase.id,
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'ref': 'INV-TEST-REF-99',
            'invoice_date': today,
            'date': today,
            'invoice_line_ids': [(0, 0, {
                'name': 'Service A',
                'account_id': self.account_expense.id,
                'price_unit': 250.0,
                'quantity': 1,
            })],
        })
        dup1.action_post()

        dup2 = self.env['account.move'].create({
            'journal_id': self.journal_purchase.id,
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'ref': 'INV-TEST-REF-99',
            'invoice_date': today,
            'date': today,
            'invoice_line_ids': [(0, 0, {
                'name': 'Service B',
                'account_id': self.account_expense.id,
                'price_unit': 350.0,
                'quantity': 1,
            })],
        })
        dup2.action_post()

        ref_alerts = self.engine._detect_duplicate_bills(
            dup1 | dup2, today - timedelta(days=10), today, [self.company.id]
        )
        self.assertTrue(ref_alerts)

    def test_16_custom_rules_types_and_constraints(self):
        """Test account_type, partner, keyword rules, and constraints."""
        today = date.today()
        # Rule by account type
        rule_acc = self.env['account.anomaly.rule'].create({
            'name': 'Expense Rule',
            'rule_type': 'account_type',
            'account_ids': [(4, self.account_expense.id)],
            'score': 25,
            'company_id': self.company.id,
        })
        self.assertEqual(rule_acc.risk_level, 'low')

        # Rule by partner
        rule_partner = self.env['account.anomaly.rule'].create({
            'name': 'Partner Watch Rule',
            'rule_type': 'partner',
            'partner_ids': [(4, self.partner.id)],
            'score': 55,
            'company_id': self.company.id,
        })
        self.assertEqual(rule_partner.risk_level, 'medium')

        # Rule by keyword
        rule_kw = self.env['account.anomaly.rule'].create({
            'name': 'Suspicious Keyword Rule',
            'rule_type': 'keyword',
            'keywords': 'kickback, confidential, bribe',
            'score': 95,
            'company_id': self.company.id,
        })
        self.assertEqual(rule_kw.risk_level, 'critical')

        # Test score constraint validation
        with self.assertRaises(ValidationError):
            self.env['account.anomaly.rule'].create({
                'name': 'Negative Score Rule',
                'rule_type': 'amount_threshold',
                'score': -5,
                'company_id': self.company.id,
            })

        # Test keyword matching on move line description
        move_kw = self.env['account.move'].create({
            'journal_id': self.journal_misc.id,
            'date': today,
            'move_type': 'entry',
            'line_ids': [
                (0, 0, {
                    'account_id': self.account_expense.id,
                    'name': 'Consulting Fee - Confidential Agreement',
                    'debit': 500.0,
                    'credit': 0.0,
                    'partner_id': self.partner.id,
                }),
                (0, 0, {
                    'account_id': self.account_cash.id,
                    'name': 'Cash Out',
                    'debit': 0.0,
                    'credit': 500.0,
                    'partner_id': self.partner.id,
                }),
            ],
        })
        move_kw.action_post()

        alerts = self.engine._detect_custom_rules(move_kw, [self.company.id])
        self.assertTrue(alerts)
        self.assertGreater(rule_kw.hits_count, 0)

    def test_17_alert_helper_computes_and_batch_actions(self):
        """Test alert colors, icons, days open, and batch operations."""
        today = date.today()
        move = self._create_misc_entry(
            self.account_expense, self.account_cash,
            500.0, today
        )
        alert = self.engine._create_alert(
            move=move,
            alert_type='duplicate_vendor_bill',
            risk_level='critical',
            title='Helper Test Alert',
            description='Testing helpers',
            score=90,
        )
        self.assertEqual(alert.risk_color, 1)
        self.assertEqual(alert.alert_type_icon, '📋')
        self.assertGreaterEqual(alert.days_open, 0)

        # Action assign to me
        alert.action_assign_to_me()
        self.assertEqual(alert.assigned_to, self.env.user)

        # Action view journal entry
        act_view = alert.action_view_journal_entry()
        self.assertEqual(act_view['res_id'], move.id)

        # Action batch false positive
        alert.action_batch_false_positive()
        self.assertEqual(alert.state, 'false_positive')

        # Action mark false positive
        alert2 = self.engine._create_alert(
            move=move,
            alert_type='manual',
            risk_level='medium',
            title='FP Test Alert',
            description='FP Testing',
            score=50,
        )
        alert2.action_mark_false_positive()
        self.assertEqual(alert2.state, 'false_positive')

        # Move action view alerts
        move_act = move.action_view_anomaly_alerts()
        self.assertEqual(move_act['res_model'], 'account.anomaly.alert')

    def test_18_cron_execution_and_format_helpers(self):
        """Test cron runner, scan branches, and formatting utilities."""
        self.company.anomaly_auto_scan_enabled = True
        self.engine._cron_run_auto_scan()

        # Run scan with no moves in date range
        empty_summary = self.engine.run_full_scan(
            date_from=date(1995, 1, 1),
            date_to=date(1995, 1, 2),
            company_ids=[self.company.id],
        )
        self.assertEqual(empty_summary['total_alerts'], 0)

        # Test currency format helper with and without currency
        fmt_no_curr = self.engine._format_currency(1234.56, None)
        self.assertEqual(fmt_no_curr, '1,234.56')
        fmt_curr = self.engine._format_currency(
            1234.56, self.company.currency_id
        )
        self.assertIn('1,234.56', fmt_curr)

    def test_19_accountant_user_scan_on_post(self):
        """Test non-anomaly accountant posting does not raise AccessError."""
        accountant = self.env['res.users'].create({
            'name': 'Test Accountant User',
            'login': 'test_accountant_no_anomaly',
            'email': 'accountant@test.example.com',
            'group_ids': [
                (6, 0, [
                    self.env.ref('base.group_user').id,
                    self.env.ref('account.group_account_invoice').id,
                ])
            ],
            'company_id': self.company.id,
            'company_ids': [(4, self.company.id)],
        })
        self.company.anomaly_scan_on_post = True
        self.company.anomaly_zscore_threshold = 2.0

        # Create baseline entries
        today = date.today()
        for i in range(6):
            self._create_misc_entry(
                self.account_expense, self.account_cash,
                100.0, today - timedelta(days=20 + i)
            )

        # Create outlier move by accountant
        outlier_move = self.env['account.move'].with_user(accountant).create({
            'journal_id': self.journal_misc.id,
            'date': today,
            'move_type': 'entry',
            'line_ids': [
                (0, 0, {
                    'account_id': self.account_expense.id,
                    'name': 'Accountant Big Expense',
                    'debit': 99999.0,
                    'credit': 0.0,
                    'partner_id': self.partner.id,
                }),
                (0, 0, {
                    'account_id': self.account_cash.id,
                    'name': 'Accountant Cash',
                    'debit': 0.0,
                    'credit': 99999.0,
                    'partner_id': self.partner.id,
                }),
            ],
        })
        # Accountant posts the move - must not fail with AccessError
        outlier_move.action_post()

        # Alert should have been generated via sudo
        alerts = self.env['account.anomaly.alert'].sudo().search([
            ('move_id', '=', outlier_move.id),
        ])
        self.assertTrue(alerts, "Scan on post by accountant must create alert")

    def test_20_multi_company_cron_sync_and_config(self):
        """Test multi-company write on res.company and per-company config."""
        company_b = self.env['res.company'].create({
            'name': 'Anomaly Test Company B',
        })
        both_companies = self.company | company_b
        # Write on both at once - should not raise Expected singleton
        both_companies.write({
            'anomaly_auto_scan_enabled': True,
            'anomaly_scan_frequency': 'weekly',
            'anomaly_vendor_concentration_pct': 45.0,
        })
        cron = self.env.ref(
            'account_anomaly_detector.cron_anomaly_daily_scan',
            raise_if_not_found=False
        )
        self.assertTrue(cron.active)
        self.assertEqual(cron.interval_type, 'weeks')

        # Test setting one company to hourly
        company_b.write({'anomaly_scan_frequency': 'hourly'})
        self.assertEqual(cron.interval_type, 'hours')

        # Test _get_config resolutions
        cfg_record = self.engine._get_config(company_b)
        self.assertEqual(cfg_record.id, company_b.id)
        cfg_id = self.engine._get_config(company_b.id)
        self.assertEqual(cfg_id.id, company_b.id)
        cfg_ctx = self.engine.with_context(
            company_id=company_b.id
        )._get_config()
        self.assertEqual(cfg_ctx.id, company_b.id)

    def test_21_rule_hits_count_precision(self):
        """Test rule hits_count does not falsely match rule:1 with rule:10."""
        rule_1 = self.env['account.anomaly.rule'].create({
            'name': 'Test Rule Prefix',
            'rule_type': 'amount_threshold',
            'min_amount': 500.0,
            'risk_level': 'high',
            'score': 70,
            'company_id': self.company.id,
        })
        fake_similar_id = rule_1.id * 10
        today = date.today()
        move = self._create_misc_entry(
            self.account_expense, self.account_cash,
            600.0, today
        )
        self.engine._create_alert(
            move=move,
            alert_type='manual',
            risk_level='high',
            title='Other Rule Alert',
            description='Test Other Rule',
            score=70,
            ml_details=f'[rule:{fake_similar_id}]',
        )
        rule_1._compute_hits_count()
        self.assertEqual(
            rule_1.hits_count, 0,
            "Rule 1 hits_count must not match [rule:10]"
        )

        # Now create alert specifically for rule_1
        self.engine._create_alert(
            move=move,
            alert_type='manual',
            risk_level='high',
            title='Rule 1 Alert',
            description='Test Rule 1',
            score=70,
            ml_details=f'[rule:{rule_1.id}]',
        )
        rule_1._compute_hits_count()
        self.assertEqual(
            rule_1.hits_count, 1,
            "Rule 1 hits_count must accurately match only [rule:1]"
        )
