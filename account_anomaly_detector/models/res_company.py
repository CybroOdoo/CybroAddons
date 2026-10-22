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
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    # ── Scan Settings ────────────────────────────────────────
    anomaly_auto_scan_enabled = fields.Boolean(
        string='Enable Automatic Scanning', default=True)
    anomaly_scan_frequency = fields.Selection([
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ], string='Scan Frequency', default='daily')
    anomaly_scan_on_post = fields.Boolean(
        string='Scan on Journal Entry Post', default=True)

    # ── Algorithm Settings ───────────────────────────────────
    anomaly_zscore_threshold = fields.Float(
        string='Z-Score Threshold', default=3.0)
    anomaly_duplicate_window_days = fields.Integer(
        string='Duplicate Detection Window (Days)', default=30)
    anomaly_round_number_threshold = fields.Float(
        string='Round Number Min Amount', default=1000.0)
    anomaly_velocity_window_days = fields.Integer(
        string='Velocity Window (Days)', default=3)
    anomaly_velocity_max_count = fields.Integer(
        string='Max Normal Transactions per Window', default=10)
    anomaly_spending_deviation_pct = fields.Float(
        string='Spending Deviation Alert Threshold (%)', default=50.0)
    anomaly_vendor_concentration_pct = fields.Float(
        string='Vendor Concentration Threshold (%)', default=40.0)
    anomaly_enable_benfords_law = fields.Boolean(
        string="Enable Benford's Law Analysis", default=True)

    # ── Notification Settings ────────────────────────────────
    anomaly_notify_critical = fields.Boolean(
        string='Notify on Critical', default=True)
    anomaly_notify_high = fields.Boolean(
        string='Notify on High', default=True)
    anomaly_notify_medium = fields.Boolean(
        string='Notify on Medium', default=False)
    anomaly_notify_low = fields.Boolean(
        string='Notify on Low', default=False)

    anomaly_notification_user_ids = fields.Many2many(
        'res.users', 'anomaly_company_users_rel',
        'company_id', 'user_id', string='Notify Users')
    anomaly_notify_auditor_group = fields.Boolean(
        string='Notify Auditor Group', default=True)

    # ── Exclusions ───────────────────────────────────────────
    anomaly_excluded_account_ids = fields.Many2many(
        'account.account', 'anomaly_company_account_rel',
        'company_id', 'account_id', string='Excluded Accounts')
    anomaly_excluded_partner_ids = fields.Many2many(
        'res.partner', 'anomaly_company_partner_rel',
        'company_id', 'partner_id', string='Excluded Partners')
    anomaly_last_scan_date = fields.Datetime(
        string='Last Anomaly Auto-Scan Date')

    def write(self, vals):
        res = super().write(vals)
        if (
            'anomaly_auto_scan_enabled' in vals
            or 'anomaly_scan_frequency' in vals
        ):
            self._sync_scan_cron()
        return res

    def _sync_scan_cron(self):
        cron = self.env.ref(
            'account_anomaly_detector.cron_anomaly_daily_scan',
            raise_if_not_found=False
        )
        if not cron:
            return
        enabled_companies = self.search([
            ('anomaly_auto_scan_enabled', '=', True)
        ])
        cron.active = bool(enabled_companies)
        if enabled_companies:
            frequencies = enabled_companies.mapped('anomaly_scan_frequency')
            if 'hourly' in frequencies:
                interval_number, interval_type = (1, 'hours')
            elif 'daily' in frequencies:
                interval_number, interval_type = (1, 'days')
            else:
                interval_number, interval_type = (1, 'weeks')
            cron.write({
                'interval_number': interval_number,
                'interval_type': interval_type,
            })
