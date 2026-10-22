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
"""
Core Anomaly Detection Engine
Uses statistical methods (Z-Score, IQR) and pattern recognition
to detect suspicious accounting transactions.
"""
import logging
import statistics
from collections import defaultdict
from datetime import timedelta

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AnomalyEngine(models.AbstractModel):
    """
    Abstract model providing ML-based anomaly detection capabilities.
    Implements:
        - Z-Score outlier detection
        - IQR-based outlier detection
        - Benford's Law analysis
        - Duplicate transaction detection
        - Velocity / frequency anomaly detection
        - Spending pattern deviation
    """
    _name = 'account.anomaly.engine'
    _description = 'Anomaly Detection Engine'

    # ─────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────

    @api.model
    def _cron_run_auto_scan(self):
        """
        Scheduled action wrapper. Iterates over all companies with auto-scan
        enabled and executes scan only for companies that are due based on
        their individual anomaly_scan_frequency setting.
        """
        now = fields.Datetime.now()
        companies = self.env['res.company'].search(
            [('anomaly_auto_scan_enabled', '=', True)]
        )
        for company in companies:
            last_scan = company.anomaly_last_scan_date
            is_due = False
            if not last_scan:
                is_due = True
            else:
                freq = company.anomaly_scan_frequency or 'daily'
                if (
                    freq == 'hourly'
                    and (now - last_scan) >= timedelta(hours=1)
                ):
                    is_due = True
                elif (
                    freq == 'daily'
                    and (now - last_scan) >= timedelta(days=1)
                ):
                    is_due = True
                elif (
                    freq == 'weekly'
                    and (now - last_scan) >= timedelta(weeks=1)
                ):
                    is_due = True

            if is_due:
                self.run_full_scan(company_ids=[company.id])
                company.sudo().write({'anomaly_last_scan_date': now})

    @api.model
    def run_full_scan(self, date_from=None, date_to=None, company_ids=None,
                      include_draft=False, algorithms=None):
        """
        Master scan entry point. Runs all detection algorithms and
        creates/updates AnomalyAlert records.
        Returns a summary dict.
        """
        if not date_from:
            date_from = fields.Date.today() - timedelta(days=30)
        if not date_to:
            date_to = fields.Date.today()
        if not company_ids:
            company_ids = self.env.companies.ids
        if company_ids and len(company_ids) == 1:
            self = self.with_context(company_id=company_ids[0])
        if algorithms is None:
            algorithms = {}

        summary = {
            'total_alerts': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'new_alerts': 0,
            'scan_date': fields.Datetime.now(),
        }

        states = ['posted']
        if include_draft:
            states.append('draft')

        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', 'in', company_ids),
            ('state', 'in', states),
            ('move_type', 'in', [
                'entry', 'out_invoice', 'in_invoice',
                'out_refund', 'in_refund'
            ]),
        ]
        moves = self.env['account.move'].search(domain)

        if not moves:
            return summary

        alerts_created = []

        # 1. Amount outlier detection
        if algorithms.get('amount_outliers', True):
            alerts_created += self._detect_amount_outliers(moves)

        # 2. Duplicate vendor bill detection
        if algorithms.get('duplicates', True):
            alerts_created += self._detect_duplicate_bills(
                moves, date_from, date_to, company_ids
            )

        # 3. Round-number bias detection
        if algorithms.get('round_numbers', True):
            alerts_created += self._detect_round_number_bias(moves)

        # 4. Velocity / burst detection
        if algorithms.get('velocity', True):
            alerts_created += self._detect_transaction_velocity(
                moves, date_from, date_to
            )

        # 5. Weekend / holiday transaction detection
        if algorithms.get('timing', True):
            alerts_created += self._detect_unusual_timing(moves)

        # 6. Spending pattern deviation by account
        if algorithms.get('spending', True):
            alerts_created += self._detect_spending_pattern_deviation(
                moves, company_ids
            )

        # 7. Benford's Law analysis
        if algorithms.get('benfords', True):
            alerts_created += self._detect_benfords_law_violation(moves)

        # 8. Unusual account combinations
        if algorithms.get('account_combos', True):
            alerts_created += self._detect_unusual_account_combinations(
                moves
            )

        # 9. Vendor concentration risk
        if algorithms.get('concentration', True):
            alerts_created += self._detect_vendor_concentration(
                moves, date_from, date_to
            )

        # 10. Custom User Rules
        alerts_created += self._detect_custom_rules(moves, company_ids)

        # Compute summary
        for alert in alerts_created:
            summary['new_alerts'] += 1
            summary[alert.risk_level] = summary.get(alert.risk_level, 0) + 1

        all_open = self.env['account.anomaly.alert'].search([
            ('state', 'in', ['open', 'investigating']),
            ('company_id', 'in', company_ids),
        ])
        summary['total_alerts'] = len(all_open)
        for a in all_open:
            summary[a.risk_level] = summary.get(a.risk_level, 0) + 1

        return summary

    # ─────────────────────────────────────────────────────────
    # Detection Algorithms
    # ─────────────────────────────────────────────────────────

    @api.model
    def _detect_custom_rules(self, moves, company_ids):
        alerts = []
        rules = self.env['account.anomaly.rule'].search([
            ('active', '=', True),
            ('company_id', 'in', company_ids)
        ])

        if not rules:
            return alerts

        for move in moves:
            for rule in rules:
                # 1. Evaluate Rule Conditions
                is_hit = False

                # Check Amount Threshold
                if rule.rule_type == 'amount_threshold':
                    amt = max(
                        abs(move.amount_total),
                        sum(line.debit for line in move.line_ids)
                    )
                    if rule.min_amount > 0 and amt >= rule.min_amount:
                        if rule.max_amount == 0 or amt <= rule.max_amount:
                            is_hit = True

                # Check Account Types
                elif rule.rule_type == 'account_type':
                    if rule.account_ids:
                        matched = move.line_ids.filtered(
                            lambda line: line.account_id in rule.account_ids
                        )
                        if matched:
                            is_hit = True

                # Check Partners
                elif rule.rule_type == 'partner':
                    if (
                        rule.partner_ids
                        and move.partner_id in rule.partner_ids
                    ):
                        is_hit = True

                # Check Keywords
                elif rule.rule_type == 'keyword':
                    if rule.keywords:
                        keywords = [
                            k.strip().lower() for k in rule.keywords.split(',')
                        ]
                        text_to_search = (
                            f"{move.name or ''} {move.ref or ''} "
                            f"{move.narration or ''}"
                        )
                        for line in move.line_ids:
                            text_to_search += f" {line.name or ''}"
                        text_to_search = text_to_search.lower()

                        if any(kw in text_to_search for kw in keywords if kw):
                            is_hit = True

                # 2. Trigger Alert if Hit
                if is_hit:
                    existing = self.env['account.anomaly.alert'].search([
                        ('move_id', '=', move.id),
                        ('alert_type', '=', 'manual'),
                        ('ml_details', 'like', f'[rule:{rule.id}]'),
                        ('state', 'not in', ['resolved', 'false_positive']),
                    ], limit=1)

                    if not existing:
                        title = (
                            rule.alert_title
                            or f"Custom Rule Violation: {rule.name}"
                        )
                        description = (
                            rule.description_template
                            or f"Transaction manually flagged by custom audit "
                               f"rule: '{rule.name}'."
                        )
                        alert = self._create_alert(
                            move=move,
                            alert_type='manual',
                            risk_level=rule.risk_level,
                            title=title,
                            description=description,
                            score=rule.score,
                        )
                        if alert:
                            alert.write({'ml_details': f'[rule:{rule.id}]'})
                            alerts.append(alert)

        return alerts

    @api.model
    def _detect_amount_outliers(self, moves):
        """
        Z-Score outlier detection on transaction amounts.
        Groups by account and detects amounts that deviate significantly.
        Applies account and partner exclusions, and queries historical
        lines when analyzing single moves.
        """
        alerts = []

        # Group amounts by account and company
        account_amounts = defaultdict(list)
        move_by_account = defaultdict(list)

        for move in moves:
            excluded_accounts = move.company_id.anomaly_excluded_account_ids
            excluded_partners = move.company_id.anomaly_excluded_partner_ids
            if move.partner_id and move.partner_id in excluded_partners:
                continue

            for line in move.line_ids:
                if (
                    line.account_id
                    and line.account_id not in excluded_accounts
                    and line.balance != 0
                ):
                    key = (
                        line.account_id.id,
                        line.account_id.code,
                        move.company_id.id,
                    )
                    account_amounts[key].append(abs(line.balance))
                    move_by_account[key].append((move, abs(line.balance)))

        for (acc_id, acc_code, comp_id), amounts in account_amounts.items():
            account = self.env['account.account'].browse(acc_id)
            comp_config = self._get_config(comp_id)
            z_threshold = comp_config.anomaly_zscore_threshold or 3.0

            # Baseline lines for this account from historical posted moves,
            # excluding the moves currently being evaluated to prevent the
            # outlier from contaminating its own baseline.
            historical_lines = self.env['account.move.line'].search([
                ('account_id', '=', acc_id),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', comp_id),
                ('balance', '!=', 0),
                ('move_id', 'not in', moves.ids),
            ], limit=100)
            hist_amounts = [abs(hl.balance) for hl in historical_lines]
            baseline_amounts = (
                hist_amounts if len(hist_amounts) >= 5 else amounts
            )
            if len(baseline_amounts) < 5:
                continue

            mean_val = statistics.mean(baseline_amounts)
            if len(baseline_amounts) >= 2:
                std_val = statistics.stdev(baseline_amounts)
            else:
                continue

            if std_val == 0:
                std_val = mean_val * 0.05 or 1.0

            # Check each move's transactions for this account
            for move, amount in move_by_account[(acc_id, acc_code, comp_id)]:
                z_score = abs(amount - mean_val) / std_val
                if z_score >= z_threshold:
                    risk = (
                        'critical' if z_score >= z_threshold * 2 else 'high'
                    )
                    existing = self._find_existing_alert(
                        move, 'amount_outlier'
                    )
                    if not existing:
                        formatted_amt = self._format_currency(
                            amount, move.currency_id
                        )
                        formatted_mean = self._format_currency(
                            mean_val, move.currency_id
                        )
                        alert = self._create_alert(
                            move=move,
                            alert_type='amount_outlier',
                            risk_level=risk,
                            title=self.env._(
                                'Unusual Transaction Amount Detected'
                            ),
                            description=self.env._(
                                'Transaction amount of %(amount)s on account '
                                '%(account)s is %(zscore).1f standard '
                                'deviations from the account mean '
                                '(avg: %(mean)s). This statistically '
                                'significant deviation requires review.',
                                amount=formatted_amt,
                                account=acc_code or account.display_name,
                                zscore=z_score,
                                mean=formatted_mean,
                            ),
                            score=min(100, int(z_score / z_threshold * 50)),
                        )
                        if alert:
                            alerts.append(alert)
                    else:
                        alerts.append(existing)
        return alerts

    @api.model
    def _detect_duplicate_bills(self, moves, date_from, date_to, company_ids):
        """
        Detects potential duplicate vendor bills by comparing:
        - Same vendor + same amount + similar date within window
        - Same vendor + same invoice reference
        """
        alerts = []

        vendor_bills = moves.filtered(
            lambda m: m.move_type == 'in_invoice'
            and m.partner_id
            and m.partner_id not in m.company_id.anomaly_excluded_partner_ids
        )

        # For single moves or targeted scans, search historical bills
        # within the duplicate window to match against.
        if len(vendor_bills) == 1 and date_from and date_to:
            single_bill = vendor_bills[0]
            ext_bills = self.env['account.move'].search([
                ('move_type', '=', 'in_invoice'),
                ('partner_id', '=', single_bill.partner_id.id),
                ('company_id', 'in', company_ids),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
            ])
            vendor_bills = vendor_bills | ext_bills

        # Group by company + partner + amount for exact duplicates
        seen = defaultdict(list)
        for bill in vendor_bills:
            key = (
                bill.company_id.id,
                bill.partner_id.id,
                round(abs(bill.amount_total), 2),
            )
            seen[key].append(bill)

        for key, bills in seen.items():
            if len(bills) < 2:
                continue
            bills_sorted = sorted(
                bills,
                key=lambda b: b.invoice_date or b.date or fields.Date.today()
            )
            for i in range(len(bills_sorted) - 1):
                b1 = bills_sorted[i]
                b2 = bills_sorted[i + 1]
                cfg = self._get_config(b1.company_id)
                days_window = cfg.anomaly_duplicate_window_days or 30
                d1 = b1.invoice_date or b1.date or fields.Date.today()
                d2 = b2.invoice_date or b2.date or fields.Date.today()
                delta = abs((d2 - d1).days) if hasattr(d2 - d1, 'days') else 0
                if delta <= days_window:
                    for dup_bill in [b1, b2]:
                        existing = self._find_existing_alert(
                            dup_bill, 'duplicate_vendor_bill'
                        )
                        if not existing:
                            alert = self._create_alert(
                                move=dup_bill,
                                alert_type='duplicate_vendor_bill',
                                risk_level='critical',
                                title=self.env._(
                                    'Potential Duplicate Vendor Bill'
                                ),
                                description=self.env._(
                                    'Bill from %(vendor)s for %(amount)s '
                                    'appears to be a duplicate. %(count)d '
                                    'bills found with identical vendor and '
                                    'amount within %(days)d days. '
                                    'Reference: %(ref)s.',
                                    vendor=dup_bill.partner_id.name,
                                    amount=self._format_currency(
                                        abs(dup_bill.amount_total),
                                        dup_bill.currency_id,
                                    ),
                                    count=len(bills),
                                    days=days_window,
                                    ref=dup_bill.ref or 'N/A',
                                ),
                                score=90,
                                related_move_ids=[
                                    (4, m.id)
                                    for m in bills
                                    if m.id != dup_bill.id
                                ],
                            )
                            if alert:
                                alerts.append(alert)

        # Check for same invoice reference from same vendor
        ref_seen = defaultdict(list)
        for bill in vendor_bills:
            if bill.ref:
                ref_key = (
                    bill.company_id.id,
                    bill.partner_id.id,
                    bill.ref.strip().upper(),
                )
                ref_seen[ref_key].append(bill)

        for ref_key, bills in ref_seen.items():
            if len(bills) >= 2:
                for dup_bill in bills:
                    existing = self._find_existing_alert(
                        dup_bill, 'duplicate_vendor_bill'
                    )
                    if not existing:
                        alert = self._create_alert(
                            move=dup_bill,
                            alert_type='duplicate_vendor_bill',
                            risk_level='critical',
                            title=self.env._(
                                'Duplicate Invoice Reference Detected'
                            ),
                            description=self.env._(
                                'Vendor %(vendor)s has %(count)d bills '
                                'with the same invoice reference "%(ref)s". '
                                'This is a strong indicator of duplicate '
                                'payment.',
                                vendor=dup_bill.partner_id.name,
                                count=len(bills),
                                ref=dup_bill.ref,
                            ),
                            score=95,
                            related_move_ids=[
                                (4, m.id)
                                for m in bills
                                if m.id != dup_bill.id
                            ],
                        )
                        if alert:
                            alerts.append(alert)
        return alerts

    @api.model
    def _detect_round_number_bias(self, moves):
        """
        Detects suspicious round-number transactions which can indicate
        fraudulent or estimated entries.
        """
        alerts = []

        for move in moves:
            comp_config = self._get_config(move.company_id)
            threshold = (
                comp_config.anomaly_round_number_threshold or 1000.0
            )
            if (
                move.partner_id
                and move.partner_id in
                comp_config.anomaly_excluded_partner_ids
            ):
                continue
            amount = max(
                abs(move.amount_total),
                sum(line.debit for line in move.line_ids)
            )
            if amount < threshold:
                continue
            is_round = (
                (amount >= 1000 and amount % 1000 == 0)
                or (amount >= 500 and amount % 500 == 0 and amount < 1000)
            )
            if is_round and amount >= threshold:
                existing = self._find_existing_alert(move, 'round_number')
                if not existing:
                    formatted_amt = self._format_currency(
                        amount, move.currency_id
                    )
                    formatted_thresh = self._format_currency(
                        threshold, move.currency_id
                    )
                    alert = self._create_alert(
                        move=move,
                        alert_type='round_number',
                        risk_level='low',
                        title=self.env._(
                            'Suspicious Round-Number Transaction'
                        ),
                        description=self.env._(
                            'Transaction of exactly %(amount)s is a round '
                            'number above threshold %(threshold)s. Round '
                            'numbers can indicate estimated or fabricated '
                            'entries. Verify supporting documentation.',
                            amount=formatted_amt,
                            threshold=formatted_thresh,
                        ),
                        score=30,
                    )
                    if alert:
                        alerts.append(alert)
        return alerts

    @api.model
    def _detect_transaction_velocity(self, moves, date_from, date_to):
        """
        Detects unusual bursts of transactions from the same partner
        within a short time window (velocity check).
        """
        alerts = []
        partner_dates = defaultdict(list)
        for move in moves:
            comp = move.company_id
            excluded = comp.anomaly_excluded_partner_ids
            if move.partner_id and move.partner_id not in excluded:
                partner_dates[(comp.id, move.partner_id.id)].append(
                    (move.invoice_date or move.date, move)
                )

        for (comp_id, partner_id), date_moves in partner_dates.items():
            comp_config = self._get_config(comp_id)
            velocity_days = comp_config.anomaly_velocity_window_days or 3
            velocity_count = comp_config.anomaly_velocity_max_count or 10
            if len(date_moves) < velocity_count:
                continue
            date_moves.sort(key=lambda x: x[0])
            for i in range(len(date_moves)):
                window_moves = []
                base_date = date_moves[i][0]
                for j in range(i, len(date_moves)):
                    d = date_moves[j][0]
                    delta = (d - base_date).days if hasattr(d, 'days') else 0
                    if delta <= velocity_days:
                        window_moves.append(date_moves[j][1])
                    else:
                        break
                if len(window_moves) >= velocity_count:
                    partner = self.env['res.partner'].browse(partner_id)
                    for move in window_moves:
                        existing = self._find_existing_alert(
                            move, 'velocity_spike'
                        )
                        if not existing:
                            alert = self._create_alert(
                                move=move,
                                alert_type='velocity_spike',
                                risk_level='high',
                                title=self.env._(
                                    'Transaction Velocity Spike'
                                ),
                                description=self.env._(
                                    '%(count)d transactions from %(partner)s '
                                    'detected within %(days)d days — '
                                    'significantly above normal velocity. '
                                    'This pattern may indicate fraudulent '
                                    'activity.',
                                    count=len(window_moves),
                                    partner=partner.name,
                                    days=velocity_days,
                                ),
                                score=70,
                            )
                            if alert:
                                alerts.append(alert)
                    break
        return alerts

    @api.model
    def _detect_unusual_timing(self, moves):
        """
        Flags transactions posted outside of normal business hours,
        on weekends, or on public holidays.
        """
        alerts = []
        for move in moves:
            excluded = move.company_id.anomaly_excluded_partner_ids
            if move.partner_id and move.partner_id in excluded:
                continue
            if not move.date:
                continue
            weekday = move.date.weekday()  # 0=Monday, 6=Sunday
            is_weekend = weekday >= 5

            if is_weekend:
                existing = self._find_existing_alert(move, 'unusual_timing')
                if not existing:
                    day_name = (
                        self.env._('Saturday')
                        if weekday == 5
                        else self.env._('Sunday')
                    )
                    alert = self._create_alert(
                        move=move,
                        alert_type='unusual_timing',
                        risk_level='medium',
                        title=self.env._('Transaction Posted on Weekend'),
                        description=self.env._(
                            'Journal entry dated %(date)s (%(day)s) was '
                            'posted outside standard business days. Weekend '
                            'postings may indicate unauthorized access or '
                            'backdating.',
                            date=move.date,
                            day=day_name,
                        ),
                        score=45,
                    )
                    if alert:
                        alerts.append(alert)
        return alerts

    @api.model
    def _detect_spending_pattern_deviation(self, moves, company_ids):
        """
        Compares current period spending per account to historical
        averages and flags significant deviations per company.
        """
        alerts = []
        today = fields.Date.today()
        baseline_from = today - timedelta(days=90)
        baseline_to = today - timedelta(days=31)
        current_from = today - timedelta(days=30)

        for comp_id in company_ids:
            comp_config = self._get_config(comp_id)
            deviation_pct = (
                (comp_config.anomaly_spending_deviation_pct or 50) / 100.0
            )
            excluded_accs = comp_config.anomaly_excluded_account_ids

            baseline_domain = [
                ('date', '>=', baseline_from),
                ('date', '<=', baseline_to),
                ('company_id', '=', comp_id),
                ('move_id.state', '=', 'posted'),
            ]
            current_domain = [
                ('date', '>=', current_from),
                ('date', '<=', today),
                ('company_id', '=', comp_id),
                ('move_id.state', 'in', ['draft', 'posted']),
            ]

            baseline_lines = self.env['account.move.line'].search(
                baseline_domain
            )
            current_lines = self.env['account.move.line'].search(
                current_domain
            )

            baseline_by_account = defaultdict(float)
            for line in baseline_lines:
                if (
                    line.account_id.account_type
                    in ['expense', 'liability_payable']
                    and line.account_id not in excluded_accs
                ):
                    balance_sum = abs(line.balance)
                    baseline_by_account[line.account_id.id] += balance_sum

            current_by_account = defaultdict(list)
            for line in current_lines:
                if (
                    line.account_id.account_type
                    in ['expense', 'liability_payable']
                    and line.account_id not in excluded_accs
                ):
                    current_by_account[line.account_id.id].append(line)

            for account_id, lines in current_by_account.items():
                if account_id not in baseline_by_account:
                    continue
                baseline_avg = baseline_by_account[account_id] / 3
                current_total = sum(abs(line.balance) for line in lines)

                if baseline_avg == 0:
                    continue

                deviation = (current_total - baseline_avg) / baseline_avg
                if deviation > deviation_pct:
                    account = self.env['account.account'].browse(account_id)
                    if lines:
                        largest_move = max(
                            lines, key=lambda line: abs(line.balance)
                        ).move_id
                        existing = self._find_existing_alert(
                            largest_move, 'spending_deviation'
                        )
                        if not existing:
                            formatted_cur = self._format_currency(
                                current_total, largest_move.currency_id
                            )
                            formatted_avg = self._format_currency(
                                baseline_avg, largest_move.currency_id
                            )
                            alert = self._create_alert(
                                move=largest_move,
                                alert_type='spending_deviation',
                                risk_level=(
                                    'high' if deviation > 1.0 else 'medium'
                                ),
                                title=self.env._(
                                    'Unusual Spending Pattern Detected'
                                ),
                                description=self.env._(
                                    'Account %(account)s shows %(pct).0f%% '
                                    'increase over 3-month average. '
                                    'Current period: %(current)s vs avg '
                                    'monthly: %(avg)s. Review for '
                                    'unauthorized or erroneous transactions.',
                                    account=account.display_name,
                                    pct=deviation * 100,
                                    current=formatted_cur,
                                    avg=formatted_avg,
                                ),
                                score=min(95, int(deviation * 50)),
                            )
                            if alert:
                                alerts.append(alert)
        return alerts

    @api.model
    def _detect_benfords_law_violation(self, moves):
        """
        Applies Benford's Law to detect fabricated numbers.
        The first digit of naturally occurring numbers follows
        a predictable logarithmic distribution.
        """
        alerts = []
        benford_expected = {
            1: 0.301, 2: 0.176, 3: 0.125, 4: 0.097,
            5: 0.079, 6: 0.067, 7: 0.058, 8: 0.051, 9: 0.046
        }

        partner_digits = defaultdict(list)
        partner_moves = defaultdict(list)

        for move in moves:
            comp_config = self._get_config(move.company_id)
            if not comp_config.anomaly_enable_benfords_law:
                continue
            excluded = comp_config.anomaly_excluded_partner_ids
            if (
                move.partner_id
                and move.partner_id not in excluded
                and abs(move.amount_total) >= 10
            ):
                num_str = str(abs(move.amount_total)).replace('.', '')
                digits_str = num_str.lstrip('0')
                if digits_str:
                    first_digit = int(digits_str[0])
                    if 1 <= first_digit <= 9:
                        key = (comp_config.id, move.partner_id.id)
                        partner_digits[key].append(first_digit)
                        partner_moves[key].append(move)

        for (comp_id, partner_id), digits in partner_digits.items():
            if len(digits) < 20:
                continue
            n = len(digits)
            observed = defaultdict(int)
            for d in digits:
                observed[d] += 1

            chi_sq = 0.0
            for digit in range(1, 10):
                expected_count = benford_expected[digit] * n
                obs_count = observed.get(digit, 0)
                if expected_count > 0:
                    chi_sq += (
                        ((obs_count - expected_count) ** 2) / expected_count
                    )

            if chi_sq > 15.5:
                partner = self.env['res.partner'].browse(partner_id)
                recent_move = partner_moves[(comp_id, partner_id)][-1]
                existing = self._find_existing_alert(
                    recent_move, 'benfords_violation'
                )
                if not existing:
                    alert = self._create_alert(
                        move=recent_move,
                        alert_type='benfords_violation',
                        risk_level='high',
                        title=self.env._("Benford's Law Violation"),
                        description=self.env._(
                            "Transactions from %(partner)s (%(count)d "
                            "entries) show statistically unusual first-digit "
                            "distribution (χ²=%(chi)0.1f, expected <15.5). "
                            "This pattern may indicate fabricated or "
                            "manipulated amounts.",
                            partner=partner.name,
                            count=n,
                            chi=chi_sq,
                        ),
                        score=75,
                    )
                    if alert:
                        alerts.append(alert)
        return alerts

    @api.model
    def _detect_unusual_account_combinations(self, moves):
        """
        Flags journal entries with unusual debit/credit account combinations
        that deviate from established patterns.
        """
        alerts = []
        high_risk_combos = [
            ('asset_cash', 'equity'),
            ('liability_payable', 'asset_receivable'),
            ('equity', 'asset_cash'),
        ]

        for move in moves:
            excluded_partners = move.company_id.anomaly_excluded_partner_ids
            excluded_accounts = move.company_id.anomaly_excluded_account_ids
            if move.partner_id and move.partner_id in excluded_partners:
                continue
            if move.move_type != 'entry':
                continue
            debit_types = set()
            credit_types = set()
            for line in move.line_ids:
                if (
                    line.account_id
                    and line.account_id in excluded_accounts
                ):
                    continue
                if line.balance > 0 and line.account_id:
                    debit_types.add(line.account_id.account_type)
                elif line.balance < 0 and line.account_id:
                    credit_types.add(line.account_id.account_type)

            for dt, ct in high_risk_combos:
                if dt in debit_types and ct in credit_types:
                    existing = self._find_existing_alert(
                        move, 'unusual_account_combo'
                    )
                    if not existing:
                        alert = self._create_alert(
                            move=move,
                            alert_type='unusual_account_combo',
                            risk_level='high',
                            title=self.env._(
                                'Unusual Account Combination in Journal Entry'
                            ),
                            description=self.env._(
                                'Journal entry %(ref)s contains an unusual '
                                'debit/credit combination: %(debit)s → '
                                '%(credit)s. This combination is rarely seen '
                                'in normal operations and requires review.',
                                ref=move.name or move.ref or 'N/A',
                                debit=dt.replace('_', ' ').title(),
                                credit=ct.replace('_', ' ').title(),
                            ),
                            score=65,
                        )
                        if alert:
                            alerts.append(alert)
        return alerts

    @api.model
    def _detect_vendor_concentration(self, moves, date_from, date_to):
        """
        Detects suspicious vendor concentration where a single vendor
        suddenly accounts for an unusually large share of spending.
        """
        alerts = []
        vendor_bills = moves.filtered(
            lambda m: m.move_type == 'in_invoice'
            and m.partner_id
            and m.state == 'posted'
            and m.partner_id not in m.company_id.anomaly_excluded_partner_ids
        )
        if not vendor_bills:
            return alerts

        bills_by_company = defaultdict(lambda: self.env['account.move'])
        for bill in vendor_bills:
            bills_by_company[bill.company_id] |= bill

        for company, comp_bills in bills_by_company.items():
            config = self._get_config(company)
            conc_threshold = (
                (config.anomaly_vendor_concentration_pct or 40) / 100.0
            )
            total_spend = sum(abs(b.amount_total) for b in comp_bills)
            if total_spend == 0:
                continue

            vendor_spend = defaultdict(float)
            vendor_moves = defaultdict(list)
            for bill in comp_bills:
                vendor_spend[bill.partner_id.id] += abs(bill.amount_total)
                vendor_moves[bill.partner_id.id].append(bill)

            for vendor_id, spend in vendor_spend.items():
                concentration = spend / total_spend
                if concentration >= conc_threshold:
                    partner = self.env['res.partner'].browse(vendor_id)
                    largest_bill = max(
                        vendor_moves[vendor_id],
                        key=lambda m: abs(m.amount_total)
                    )
                    existing = self._find_existing_alert(
                        largest_bill, 'vendor_concentration'
                    )
                    if not existing:
                        formatted_spend = self._format_currency(
                            spend, largest_bill.currency_id
                        )
                        formatted_total = self._format_currency(
                            total_spend, largest_bill.currency_id
                        )
                        alert = self._create_alert(
                            move=largest_bill,
                            alert_type='vendor_concentration',
                            risk_level='medium',
                            title=self.env._(
                                'High Vendor Concentration Risk'
                            ),
                            description=self.env._(
                                '%(vendor)s accounts for %(pct).0f%% of '
                                'total vendor spend (%(amount)s of %(total)s) '
                                'in the current period. High vendor '
                                'concentration may indicate preferential '
                                'treatment or control weakness.',
                                vendor=partner.name,
                                pct=concentration * 100,
                                amount=formatted_spend,
                                total=formatted_total,
                            ),
                            score=50,
                        )
                        if alert:
                            alerts.append(alert)
        return alerts

    # ─────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────

    @api.model
    def _get_config(self, company=None):
        if isinstance(company, int):
            return self.env['res.company'].browse(company)
        if company:
            return company
        comp_id = (
            self.env.context.get('force_company')
            or self.env.context.get('company_id')
            or self.env.context.get('default_company_id')
        )
        if comp_id:
            return self.env['res.company'].browse(comp_id)
        return self.env.company

    @api.model
    def _find_existing_alert(self, move, alert_type):
        return self.env['account.anomaly.alert'].search([
            ('move_id', '=', move.id),
            ('alert_type', '=', alert_type),
            ('state', 'not in', ['resolved', 'false_positive']),
        ], limit=1)

    @api.model
    def _create_alert(self, move, alert_type, risk_level, title, description,
                      score=50, related_move_ids=None, ml_details=None):
        company = move.company_id
        if (
            move.partner_id
            and move.partner_id in company.anomaly_excluded_partner_ids
        ):
            return None

        vals = {
            'move_id': move.id,
            'alert_type': alert_type,
            'risk_level': risk_level,
            'title': title,
            'description': description,
            'anomaly_score': score,
            'company_id': company.id,
            'detected_date': fields.Datetime.now(),
            'state': 'open',
        }
        if related_move_ids:
            vals['related_move_ids'] = related_move_ids
        if ml_details:
            vals['ml_details'] = ml_details
        try:
            alert = self.env['account.anomaly.alert'].create(vals)
            _logger.info(
                "Anomaly alert created: %s for move %s", alert_type, move.name
            )
        except Exception as e:
            _logger.error("Failed to create anomaly alert: %s", str(e))
            return None

        # Notifications
        try:
            self._dispatch_notification(alert, company, risk_level)
        except Exception as ex:
            _logger.warning("Notification dispatch failed: %s", ex)
        return alert

    @api.model
    def _dispatch_notification(self, alert, company, risk_level):
        """Notify configured auditor group or users on alert creation."""
        notify_enabled = (
            (risk_level == 'critical' and company.anomaly_notify_critical)
            or (risk_level == 'high' and company.anomaly_notify_high)
            or (risk_level == 'medium' and company.anomaly_notify_medium)
            or (risk_level == 'low' and company.anomaly_notify_low)
        )
        if not notify_enabled:
            return

        recipients = self.env['res.users']
        if company.anomaly_notify_auditor_group:
            auditor_group = self.env.ref(
                'account_anomaly_detector.group_anomaly_viewer',
                raise_if_not_found=False
            )
            if auditor_group:
                recipients |= auditor_group.user_ids
        if company.anomaly_notification_user_ids:
            recipients |= company.anomaly_notification_user_ids

        partners = recipients.mapped('partner_id')
        if partners:
            try:
                alert.message_notify(
                    partner_ids=partners.ids,
                    subject=alert.title,
                    body=alert.description,
                )
            except Exception as ex:
                _logger.warning(
                    "Could not dispatch alert notification: %s", ex
                )

    @api.model
    def _format_currency(self, amount, currency=None):
        if currency:
            return f"{currency.symbol}{amount:,.2f}"
        return f"{amount:,.2f}"
