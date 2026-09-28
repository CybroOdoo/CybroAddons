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

class ResConfigSettings(models.TransientModel):
    """
    Inherits res.config.settings to expose company-level AI anomaly detection parameters,
    algorithm sensitivity controls, and notification settings in the global Settings UI.
    """
    _inherit = 'res.config.settings'

    # ── Scan Settings ────────────────────────────────────────
    anomaly_auto_scan_enabled = fields.Boolean(
        related='company_id.anomaly_auto_scan_enabled', readonly=False,
        help="Enable automated background scanning for accounting anomalies.")
    anomaly_scan_frequency = fields.Selection(
        related='company_id.anomaly_scan_frequency', readonly=False,
        help="Frequency interval for background automated anomaly scans.")
    anomaly_scan_on_post = fields.Boolean(
        related='company_id.anomaly_scan_on_post', readonly=False,
        help="Automatically perform anomaly detection on journal entries as soon as they are posted.")
    # ── Algorithm Settings ───────────────────────────────────
    anomaly_zscore_threshold = fields.Float(
        related='company_id.anomaly_zscore_threshold', readonly=False,
        help="Z-Score statistical threshold for identifying extreme transaction amount outliers.")
    anomaly_duplicate_window_days = fields.Integer(
        related='company_id.anomaly_duplicate_window_days', readonly=False,
        help="Time window in days to check backwards for duplicate vendor bills.")
    anomaly_round_number_threshold = fields.Float(
        related='company_id.anomaly_round_number_threshold', readonly=False,
        help="Minimum transaction amount above which round-number bias is evaluated.")
    anomaly_velocity_window_days = fields.Integer(
        related='company_id.anomaly_velocity_window_days', readonly=False,
        help="Number of days in the sliding window to evaluate transaction velocity bursts.")
    anomaly_velocity_max_count = fields.Integer(
        related='company_id.anomaly_velocity_max_count', readonly=False,
        help="Maximum normal number of transactions allowed per velocity window before flagging a burst.")
    anomaly_spending_deviation_pct = fields.Float(
        related='company_id.anomaly_spending_deviation_pct', readonly=False,
        help="Percentage deviation threshold from historical average spending to trigger an alert.")
    anomaly_vendor_concentration_pct = fields.Float(
        related='company_id.anomaly_vendor_concentration_pct', readonly=False,
        help="Percentage threshold of total spending with a single vendor to trigger concentration risk.")
    anomaly_enable_benfords_law = fields.Boolean(
        related='company_id.anomaly_enable_benfords_law', readonly=False,
        help="Enable Benford's Law first-digit statistical analysis on vendor balances.")

    # ── Notification Settings ────────────────────────────────
    anomaly_notify_critical = fields.Boolean(
        related='company_id.anomaly_notify_critical', readonly=False,
        help="Send notifications when critical risk alerts are detected.")
    anomaly_notify_high = fields.Boolean(
        related='company_id.anomaly_notify_high', readonly=False,
        help="Send notifications when high risk alerts are detected.")
    anomaly_notify_medium = fields.Boolean(
        related='company_id.anomaly_notify_medium', readonly=False,
        help="Send notifications when medium risk alerts are detected.")
    anomaly_notify_low = fields.Boolean(
        related='company_id.anomaly_notify_low', readonly=False,
        help="Send notifications when low risk alerts are detected.")
    
    anomaly_notification_user_ids = fields.Many2many(
        related='company_id.anomaly_notification_user_ids', readonly=False,
        help="Specific users who receive anomaly detection notification emails.")
    anomaly_notify_auditor_group = fields.Boolean(
        related='company_id.anomaly_notify_auditor_group', readonly=False,
        help="Send anomaly notifications to all members of the Auditor user group.")

    # ── Exclusions ───────────────────────────────────────────
    anomaly_excluded_account_ids = fields.Many2many(
        related='company_id.anomaly_excluded_account_ids', readonly=False,
        help="Specific accounts excluded from all automated anomaly scans.")
    anomaly_excluded_partner_ids = fields.Many2many(
        related='company_id.anomaly_excluded_partner_ids', readonly=False,
        help="Specific partners excluded from all automated anomaly scans.")
