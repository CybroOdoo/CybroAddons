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
    _inherit = 'res.config.settings'

    # ── Scan Settings ────────────────────────────────────────
    anomaly_auto_scan_enabled = fields.Boolean(
        related='company_id.anomaly_auto_scan_enabled', readonly=False)
    anomaly_scan_frequency = fields.Selection(
        related='company_id.anomaly_scan_frequency', readonly=False)
    anomaly_scan_on_post = fields.Boolean(
        related='company_id.anomaly_scan_on_post', readonly=False)

    # ── Algorithm Settings ───────────────────────────────────
    anomaly_zscore_threshold = fields.Float(
        related='company_id.anomaly_zscore_threshold', readonly=False)
    anomaly_duplicate_window_days = fields.Integer(
        related='company_id.anomaly_duplicate_window_days', readonly=False)
    anomaly_round_number_threshold = fields.Float(
        related='company_id.anomaly_round_number_threshold', readonly=False)
    anomaly_velocity_window_days = fields.Integer(
        related='company_id.anomaly_velocity_window_days', readonly=False)
    anomaly_velocity_max_count = fields.Integer(
        related='company_id.anomaly_velocity_max_count', readonly=False)
    anomaly_spending_deviation_pct = fields.Float(
        related='company_id.anomaly_spending_deviation_pct', readonly=False)
    anomaly_vendor_concentration_pct = fields.Float(
        related='company_id.anomaly_vendor_concentration_pct', readonly=False)
    anomaly_enable_benfords_law = fields.Boolean(
        related='company_id.anomaly_enable_benfords_law', readonly=False)

    # ── Notification Settings ────────────────────────────────
    anomaly_notify_critical = fields.Boolean(
        related='company_id.anomaly_notify_critical', readonly=False)
    anomaly_notify_high = fields.Boolean(
        related='company_id.anomaly_notify_high', readonly=False)
    anomaly_notify_medium = fields.Boolean(
        related='company_id.anomaly_notify_medium', readonly=False)
    anomaly_notify_low = fields.Boolean(
        related='company_id.anomaly_notify_low', readonly=False)
    
    anomaly_notification_user_ids = fields.Many2many(
        related='company_id.anomaly_notification_user_ids', readonly=False)
    anomaly_notify_auditor_group = fields.Boolean(
        related='company_id.anomaly_notify_auditor_group', readonly=False)

    # ── Exclusions ───────────────────────────────────────────
    anomaly_excluded_account_ids = fields.Many2many(
        related='company_id.anomaly_excluded_account_ids', readonly=False)
    anomaly_excluded_partner_ids = fields.Many2many(
        related='company_id.anomaly_excluded_partner_ids', readonly=False)
