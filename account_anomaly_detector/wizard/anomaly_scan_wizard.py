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
from odoo import models, fields, _
from odoo.exceptions import UserError
from datetime import timedelta


class AnomalyScanWizard(models.TransientModel):
    _name = 'account.anomaly.scan.wizard'
    _description = 'Run Anomaly Detection Scan'

    date_from = fields.Date(
        string='From Date',
        default=lambda self: fields.Date.today() - timedelta(days=30),
        required=True)
    date_to = fields.Date(
        string='To Date',
        default=fields.Date.today,
        required=True)
    company_ids = fields.Many2many(
        'res.company', string='Companies',
        default=lambda self: self.env.companies)
    scan_all = fields.Boolean(
        string='Include Draft Entries', default=False)

    # Algorithm toggles
    scan_amount_outliers = fields.Boolean(
        string='Amount Outliers', default=True)
    scan_duplicates = fields.Boolean(
        string='Duplicate Bills', default=True)
    scan_round_numbers = fields.Boolean(
        string='Round Numbers', default=True)
    scan_velocity = fields.Boolean(
        string='Transaction Velocity', default=True)
    scan_timing = fields.Boolean(
        string='Unusual Timing', default=True)
    scan_spending = fields.Boolean(
        string='Spending Patterns', default=True)
    scan_benfords = fields.Boolean(
        string="Benford's Law", default=True)
    scan_account_combos = fields.Boolean(
        string='Account Combinations', default=True)
    scan_concentration = fields.Boolean(
        string='Vendor Concentration', default=True)

    def action_run_scan(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_("'From Date' must be before 'To Date'."))

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
            'view_mode': 'list,form',
            'domain': [
                ('state', 'in', ['open', 'investigating', 'escalated']),
            ],
            'context': {
                'search_default_open': 1,
                'anomaly_scan_summary': summary,
            },
        }
