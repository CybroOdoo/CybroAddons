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
from odoo.exceptions import UserError


class AccountAnomalyAlert(models.Model):
    _name = 'account.anomaly.alert'
    _description = 'Accounting Anomaly Alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'anomaly_score desc, detected_date desc'
    _rec_name = 'title'

    # ── Identification ───────────────────────────────────────
    title = fields.Char(string='Alert Title', required=True, tracking=True)
    description = fields.Text(string='Description', required=True)
    alert_type = fields.Selection([
        ('amount_outlier', 'Amount Outlier'),
        ('duplicate_vendor_bill', 'Duplicate Vendor Bill'),
        ('round_number', 'Round Number Bias'),
        ('velocity_spike', 'Transaction Velocity Spike'),
        ('unusual_timing', 'Unusual Timing'),
        ('spending_deviation', 'Spending Pattern Deviation'),
        ('benfords_violation', "Benford's Law Violation"),
        ('unusual_account_combo', 'Unusual Account Combination'),
        ('vendor_concentration', 'Vendor Concentration Risk'),
        ('manual', 'Manual Flag'),
    ], string='Alert Type', required=True, tracking=True)

    alert_type_icon = fields.Char(
        string='Type Icon', compute='_compute_type_icon', store=False)

    # ── Risk Assessment ──────────────────────────────────────
    risk_level = fields.Selection([
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string='Risk Level', required=True, default='medium', tracking=True)

    anomaly_score = fields.Integer(
        string='Anomaly Score', default=50,
        help='0-100 score indicating anomaly severity. 100 = most suspicious.')

    # ── Status ───────────────────────────────────────────────
    state = fields.Selection([
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved - Legitimate'),
        ('false_positive', 'False Positive'),
        ('escalated', 'Escalated'),
    ], string='Status', default='open', required=True, tracking=True)

    # ── Related Records ──────────────────────────────────────
    move_id = fields.Many2one(
        'account.move', string='Journal Entry', ondelete='cascade', index=True)
    related_move_ids = fields.Many2many(
        'account.move', 'anomaly_alert_move_rel', 'alert_id', 'move_id',
        string='Related Entries')
    partner_id = fields.Many2one(
        'res.partner', string='Partner', related='move_id.partner_id', store=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company)

    # ── Dates ────────────────────────────────────────────────
    detected_date = fields.Datetime(
        string='Detected On', default=fields.Datetime.now, readonly=True)
    resolved_date = fields.Datetime(string='Resolved On', readonly=True)

    # ── Resolution ───────────────────────────────────────────
    resolution_note = fields.Text(string='Resolution Notes')
    assigned_to = fields.Many2one('res.users', string='Assigned To', tracking=True)
    reviewed_by = fields.Many2one('res.users', string='Reviewed By', readonly=True)

    # ── ML Details ───────────────────────────────────────────
    ml_details = fields.Text(string='ML Analysis Details')
    detection_method = fields.Char(string='Detection Method')

    # ── Computed ─────────────────────────────────────────────
    move_amount = fields.Monetary(
        string='Transaction Amount',
        related='move_id.amount_total',
        currency_field='currency_id')
    currency_id = fields.Many2one(
        related='move_id.currency_id', string='Currency')
    move_date = fields.Date(
        string='Transaction Date', related='move_id.date')
    move_ref = fields.Char(
        string='Reference', related='move_id.ref')

    risk_color = fields.Integer(
        string='Risk Color', compute='_compute_risk_color', store=False)

    days_open = fields.Integer(
        string='Days Open', compute='_compute_days_open', store=False)

    # ─────────────────────────────────────────────────────────
    # Computed Methods
    # ─────────────────────────────────────────────────────────

    @api.depends('risk_level')
    def _compute_risk_color(self):
        color_map = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
        for rec in self:
            rec.risk_color = color_map.get(rec.risk_level, 4)

    @api.depends('alert_type')
    def _compute_type_icon(self):
        icon_map = {
            'amount_outlier': '📊',
            'duplicate_vendor_bill': '📋',
            'round_number': '🔢',
            'velocity_spike': '⚡',
            'unusual_timing': '🕐',
            'spending_deviation': '📈',
            'benfords_violation': '🔬',
            'unusual_account_combo': '⚠️',
            'vendor_concentration': '🏢',
            'manual': '✏️',
        }
        for rec in self:
            rec.alert_type_icon = icon_map.get(rec.alert_type, '❓')

    @api.depends('detected_date', 'state')
    def _compute_days_open(self):
        today = fields.Datetime.now()
        for rec in self:
            if rec.detected_date and rec.state in ['open', 'investigating', 'escalated']:
                delta = today - rec.detected_date
                rec.days_open = delta.days
            else:
                rec.days_open = 0

    # ─────────────────────────────────────────────────────────
    # Actions
    # ─────────────────────────────────────────────────────────

    def action_investigate(self):
        self.ensure_one()
        self.write({
            'state': 'investigating',
            'assigned_to': self.env.user.id,
        })
        self.message_post(
            body=_("Alert moved to 'Under Investigation' by %s") % self.env.user.name)

    def action_resolve(self):
        self.ensure_one()
        if not self.resolution_note:
            raise UserError(_("Please provide resolution notes before resolving."))
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Datetime.now(),
            'reviewed_by': self.env.user.id,
        })
        self.message_post(
            body=_("Alert resolved by %s. Note: %s") % (
                self.env.user.name, self.resolution_note))

    def action_mark_false_positive(self):
        self.ensure_one()
        self.write({
            'state': 'false_positive',
            'resolved_date': fields.Datetime.now(),
            'reviewed_by': self.env.user.id,
        })
        self.message_post(
            body=_("Marked as False Positive by %s") % self.env.user.name)

    def action_escalate(self):
        self.ensure_one()
        self.write({'state': 'escalated'})
        self.message_post(
            body=_("Alert escalated by %s") % self.env.user.name)

    def action_view_journal_entry(self):
        self.ensure_one()
        if not self.move_id:
            raise UserError(_("No journal entry linked to this alert."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_assign_to_me(self):
        self.write({'assigned_to': self.env.user.id})

    # ─────────────────────────────────────────────────────────
    # Batch Actions
    # ─────────────────────────────────────────────────────────

    def action_batch_resolve(self):
        for rec in self:
            if rec.state not in ['resolved', 'false_positive']:
                rec.write({
                    'state': 'resolved',
                    'resolved_date': fields.Datetime.now(),
                    'reviewed_by': self.env.user.id,
                    'resolution_note': rec.resolution_note or 'Batch resolved',
                })

    def action_batch_false_positive(self):
        for rec in self:
            if rec.state not in ['resolved', 'false_positive']:
                rec.write({
                    'state': 'false_positive',
                    'resolved_date': fields.Datetime.now(),
                    'reviewed_by': self.env.user.id,
                })

    # ─────────────────────────────────────────────────────────
    # Constraints
    # ─────────────────────────────────────────────────────────

    @api.constrains('anomaly_score')
    def _check_anomaly_score(self):
        for rec in self:
            if not (0 <= rec.anomaly_score <= 100):
                raise UserError(_("Anomaly score must be between 0 and 100."))
