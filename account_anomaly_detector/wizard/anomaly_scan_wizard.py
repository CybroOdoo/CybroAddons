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
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class AnomalyScanWizard(models.TransientModel):
    """
    Transient model wizard allowing auditors to run targeted, on-demand anomaly detection scans
    across custom date ranges, companies, and selected detection algorithms.
    """
    _name = 'account.anomaly.scan.wizard'
    _description = 'Run Anomaly Detection Scan'

    date_from = fields.Date(
        string='From Date',
        default=lambda self: fields.Date.today() - timedelta(days=30),
        required=True,
        help="Start date of the date range to scan for accounting anomalies.")
    date_to = fields.Date(
        string='To Date',
        default=fields.Date.today,
        required=True,
        help="End date of the date range to scan for accounting anomalies.")
    company_ids = fields.Many2many(
        'res.company', string='Companies',
        default=lambda self: self.env.companies,
        help="Companies whose general ledger entries will be scanned.")
    scan_all = fields.Boolean(
        string='Include Draft Entries', default=False,
        help="Include unposted draft journal entries in the anomaly scan.")

    # Algorithm toggles
    scan_amount_outliers = fields.Boolean(
        string='Amount Outliers', default=True,
        help="Toggle Z-Score and IQR statistical amount outlier detection.")
    scan_duplicates = fields.Boolean(
        string='Duplicate Bills', default=True,
        help="Toggle duplicate vendor bill and invoice detection.")
    scan_round_numbers = fields.Boolean(
        string='Round Numbers', default=True,
        help="Toggle round-number bias anomaly detection.")
    scan_velocity = fields.Boolean(
        string='Transaction Velocity', default=True,
        help="Toggle transaction velocity and burst frequency detection.")
    scan_timing = fields.Boolean(
        string='Unusual Timing', default=True,
        help="Toggle weekend and holiday unusual timing detection.")
    scan_spending = fields.Boolean(
        string='Spending Patterns', default=True,
        help="Toggle spending pattern deviation analysis.")
    scan_benfords = fields.Boolean(
        string="Benford's Law", default=True,
        help="Toggle Benford's Law first-digit statistical analysis.")
    scan_account_combos = fields.Boolean(
        string='Account Combinations', default=True,
        help="Toggle unusual account combination analysis.")
    scan_concentration = fields.Boolean(
        string='Vendor Concentration', default=True,
        help="Toggle vendor concentration risk analysis.")

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        """Provide instant interactive validation warning when selecting date fields."""
        today = fields.Date.today()
        if self.date_from and self.date_to and self.date_from > self.date_to:
            return {
                'warning': {
                    'title': _("Invalid Date Selection"),
                    'message': _("'From Date' (%s) cannot be greater than 'To Date' (%s).",
                                 self.date_from, self.date_to),
                }
            }
        if self.date_from and self.date_from > today:
            return {
                'warning': {
                    'title': _("Invalid Date Selection"),
                    'message': _("'From Date' (%s) cannot be in the future.", self.date_from),
                }
            }
        if self.date_to and self.date_to > today:
            return {
                'warning': {
                    'title': _("Invalid Date Selection"),
                    'message': _("'To Date' (%s) cannot be in the future.", self.date_to),
                }
            }

    @api.constrains('date_from', 'date_to')
    def _check_date_fields(self):
        """Validate date_from and date_to fields before saving or running scan."""
        today = fields.Date.today()
        for record in self:
            if record.date_from and record.date_to:
                if record.date_from > record.date_to:
                    raise ValidationError(_("'From Date' (%(date_from)s) cannot be greater than 'To Date' (%(date_to)s).",
                        date_from=record.date_from, date_to=record.date_to))
                if record.date_from > today:
                    raise ValidationError(_("'From Date' (%s) cannot be in the future.", record.date_from))
                if record.date_to > today:
                    raise ValidationError(_("'To Date' (%s) cannot be in the future.", record.date_to))

    def action_run_scan(self):
        """Execute on-demand anomaly scan with configured parameters and return action opening resulting alert list."""
        self.ensure_one()
        self._check_date_fields()

        algorithms = {
            'amount_outliers': self.scan_amount_outliers,
            'duplicates': self.scan_duplicates,
            'round_numbers': self.scan_round_numbers,
            'velocity': self.scan_velocity,
            'timing': self.scan_timing,
            'spending': self.scan_spending,
            'benfords': self.scan_benfords,
            'account_combos': self.scan_account_combos,
            'concentration': self.scan_concentration,
        }

        engine = self.env['account.anomaly.engine']
        summary = engine.run_full_scan(
            date_from=self.date_from,
            date_to=self.date_to,
            company_ids=self.company_ids.ids or self.env.companies.ids,
            include_draft=self.scan_all,
            algorithms=algorithms,
        )

        # Return to alert list with a notification
        return {
            'type': 'ir.actions.act_window',
            'name': _('Anomaly Alerts'),
            'res_model': 'account.anomaly.alert',
            'view_mode': 'tree,form',
            'domain': [('state', 'in', ['open', 'investigating', 'escalated'])],
            'context': {
                'search_default_open': 1,
                'anomaly_scan_summary': summary,
            },
        }
