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


class AccountMove(models.Model):
    _inherit = 'account.move'

    anomaly_alert_ids = fields.One2many(
        'account.anomaly.alert', 'move_id',
        string='Anomaly Alerts')

    anomaly_alert_count = fields.Integer(
        string='Anomaly Alerts',
        compute='_compute_anomaly_alert_count',
        store=True)

    anomaly_risk_level = fields.Selection([
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('clean', 'No Issues'),
    ], string='Risk Level', compute='_compute_anomaly_risk_level', store=True)

    @api.depends('anomaly_alert_ids', 'anomaly_alert_ids.state')
    def _compute_anomaly_alert_count(self):
        for move in self:
            move.anomaly_alert_count = len(
                move.anomaly_alert_ids.filtered(
                    lambda a: a.state not in ['resolved', 'false_positive']
                )
            )

    @api.depends('anomaly_alert_ids', 'anomaly_alert_ids.risk_level',
                 'anomaly_alert_ids.state')
    def _compute_anomaly_risk_level(self):
        priority = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'clean': 0}
        for move in self:
            active_alerts = move.anomaly_alert_ids.filtered(
                lambda a: a.state not in ['resolved', 'false_positive']
            )
            if not active_alerts:
                move.anomaly_risk_level = 'clean'
            else:
                worst = max(active_alerts, key=lambda a: priority.get(a.risk_level, 0))
                move.anomaly_risk_level = worst.risk_level

    def action_post(self):
        """Override to run anomaly detection on posting."""
        result = super().action_post()
        # Run scan for newly posted entries if config enabled
        for move in self:
            if move.company_id.anomaly_scan_on_post:
                try:
                    engine = self.env['account.anomaly.engine']
                    engine._detect_amount_outliers(move)
                    engine._detect_duplicate_bills(
                        move, move.date, move.date, [move.company_id.id])
                    engine._detect_unusual_timing(move)
                except Exception:
                    pass  # Never block posting due to anomaly detection errors
        return result

    def action_view_anomaly_alerts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Anomaly Alerts'),
            'res_model': 'account.anomaly.alert',
            'view_mode': 'list,form',
            'domain': [('move_id', '=', self.id)],
            'context': {'default_move_id': self.id},
        }
