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
from odoo import models, fields

class ResCompany(models.Model):
    """
    Inherits res.company to store company-wide configuration settings for AI anomaly detection,
    algorithm sensitivity parameters, automated notification options, and exclusion filters.
    """
    _inherit = 'res.company'

    # ── Scan Settings ────────────────────────────────────────
    anomaly_auto_scan_enabled = fields.Boolean(
        string='Enable Automatic Scanning', default=True,
        help="Enable automated background scanning for accounting anomalies.")
    anomaly_scan_frequency = fields.Selection([
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ], string='Scan Frequency', default='daily',
       help="Frequency interval for background automated anomaly scans.")
    anomaly_scan_on_post = fields.Boolean(
        string='Scan on Journal Entry Post', default=True,
        help="Automatically perform anomaly detection on journal entries as soon as they are posted.")

    # ── Algorithm Settings ───────────────────────────────────
    anomaly_zscore_threshold = fields.Float(
        string='Z-Score Threshold', default=3.0,
        help="Z-Score statistical threshold for identifying extreme transaction amount outliers.")
    anomaly_duplicate_window_days = fields.Integer(
        string='Duplicate Detection Window (Days)', default=30,
        help="Time window in days to check backwards for duplicate vendor bills.")
    anomaly_round_number_threshold = fields.Float(
        string='Round Number Min Amount', default=1000.0,
        help="Minimum transaction amount above which round-number bias is evaluated.")
    anomaly_velocity_window_days = fields.Integer(
        string='Velocity Window (Days)', default=3,
        help="Number of days in the sliding window to evaluate transaction velocity bursts.")
    anomaly_velocity_max_count = fields.Integer(
        string='Max Normal Transactions per Window', default=10,
        help="Maximum normal number of transactions allowed per velocity window before flagging a burst.")
    anomaly_spending_deviation_pct = fields.Float(
        string='Spending Deviation Alert Threshold (%)', default=50.0,
        help="Percentage deviation threshold from historical average spending to trigger an alert.")
    anomaly_vendor_concentration_pct = fields.Float(
        string='Vendor Concentration Threshold (%)', default=40.0,
        help="Percentage threshold of total spending with a single vendor to trigger concentration risk.")
    anomaly_enable_benfords_law = fields.Boolean(
        string="Enable Benford's Law Analysis", default=True,
        help="Enable Benford's Law first-digit statistical analysis on vendor balances.")

    # ── Notification Settings ────────────────────────────────
    anomaly_notify_critical = fields.Boolean(
        string='Notify on Critical', default=True,
        help="Send notifications when critical risk alerts are detected.")
    anomaly_notify_high = fields.Boolean(
        string='Notify on High', default=True,
        help="Send notifications when high risk alerts are detected.")
    anomaly_notify_medium = fields.Boolean(
        string='Notify on Medium', default=False,
        help="Send notifications when medium risk alerts are detected.")
    anomaly_notify_low = fields.Boolean(
        string='Notify on Low', default=False,
        help="Send notifications when low risk alerts are detected.")
    
    anomaly_notification_user_ids = fields.Many2many(
        'res.users', 'anomaly_company_users_rel', 'company_id', 'user_id',
        string='Notify Users',
        help="Specific users who receive anomaly detection notification emails.")
    anomaly_notify_auditor_group = fields.Boolean(
        string='Notify Auditor Group', default=True,
        help="Send anomaly notifications to all members of the Auditor user group.")

    # ── Exclusions ───────────────────────────────────────────
    anomaly_excluded_account_ids = fields.Many2many(
        'account.account', 'anomaly_company_account_rel', 'company_id', 'account_id',
        string='Excluded Accounts',
        help="Specific accounts excluded from all automated anomaly scans.")
    anomaly_excluded_partner_ids = fields.Many2many(
        'res.partner', 'anomaly_company_partner_rel', 'company_id', 'partner_id',
        string='Excluded Partners',
        help="Specific partners excluded from all automated anomaly scans.")
