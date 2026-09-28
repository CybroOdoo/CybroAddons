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
    """
    Represents an AI-detected or manually flagged accounting anomaly alert with risk scoring,
    machine learning details, and investigation lifecycle workflow.
    """
    _name = 'account.anomaly.alert'
    _description = 'Accounting Anomaly Alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'anomaly_score desc, detected_date desc'
    _rec_name = 'title'

    # ── Identification ───────────────────────────────────────
    title = fields.Char(
        string='Alert Title', required=True, tracking=True,
        help="Descriptive title of the anomaly alert.")
    description = fields.Text(
        string='Description', required=True,
        help="Detailed description explaining why this transaction was flagged.")
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
    ], string='Alert Type', required=True, tracking=True,
       help="Categorization of the detected anomaly pattern.")

    alert_type_icon = fields.Char(
        string='Type Icon', compute='_compute_type_icon', store=False,
        help="Emoji icon corresponding to the alert category.")

    # ── Risk Assessment ──────────────────────────────────────
    risk_level = fields.Selection([
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string='Risk Level', compute='_compute_risk_level', store=True, precompute=True, default='low', readonly=False, required=True, tracking=True,
       help="Assessed risk level automatically computed from the anomaly score.")

    anomaly_score = fields.Integer(
        string='Anomaly Score', default=50,
        help="0-100 score indicating anomaly severity. 100 = most suspicious.")

    @api.depends('anomaly_score')
    def _compute_risk_level(self):
        """Compute risk level based on anomaly score thresholds (0-30 Low, 31-60 Medium, 61-90 High, 91-100 Critical)."""
        for rec in self:
            score = rec.anomaly_score or 0
            if score <= 30:
                rec.risk_level = 'low'
            elif score <= 60:
                rec.risk_level = 'medium'
            elif score <= 90:
                rec.risk_level = 'high'
            else:
                rec.risk_level = 'critical'

    # ── Status ───────────────────────────────────────────────
    state = fields.Selection([
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved - Legitimate'),
        ('false_positive', 'False Positive'),
        ('escalated', 'Escalated'),
    ], string='Status', default='open', required=True, tracking=True,
       help="Current investigation state of the anomaly alert.")

    # ── Related Records ──────────────────────────────────────
    move_id = fields.Many2one(
        'account.move', string='Journal Entry', ondelete='cascade', index=True,
        help="Primary journal entry flagged by this alert.")
    related_move_ids = fields.Many2many(
        'account.move', 'anomaly_alert_move_rel', 'alert_id', 'move_id',
        string='Related Entries',
        help="Additional related journal entries involved in the anomaly pattern.")
    partner_id = fields.Many2one(
        'res.partner', string='Partner', related='move_id.partner_id', store=True,
        help="Partner associated with the flagged journal entry.")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company,
        help="Company owning the flagged transaction.")

    # ── Dates ────────────────────────────────────────────────
    detected_date = fields.Datetime(
        string='Detected On', default=fields.Datetime.now, readonly=True,
        help="Date and time when the anomaly was detected.")
    resolved_date = fields.Datetime(
        string='Resolved On', readonly=True,
        help="Date and time when the alert was marked as resolved or false positive.")

    # ── Resolution ───────────────────────────────────────────
    resolution_note = fields.Text(
        string='Resolution Notes',
        help="Auditor notes explaining resolution or justification.")
    assigned_to = fields.Many2one(
        'res.users', string='Assigned To', tracking=True,
        help="Auditor or team member assigned to investigate this alert.")
    reviewed_by = fields.Many2one(
        'res.users', string='Reviewed By', readonly=True,
        help="User who reviewed and resolved or closed this alert.")

    # ── ML Details ───────────────────────────────────────────
    ml_details = fields.Text(
        string='ML Analysis Details',
        help="Technical parameters and mathematical calculations behind the detection.")
    detection_method = fields.Char(
        string='Detection Method',
        help="Name of the specific algorithm or rule that flagged this alert.")

    # ── Computed ─────────────────────────────────────────────
    move_amount = fields.Monetary(
        string='Transaction Amount',
        related='move_id.amount_total',
        currency_field='currency_id',
        help="Total monetary amount of the flagged transaction.")
    currency_id = fields.Many2one(
        related='move_id.currency_id', string='Currency',
        help="Currency of the transaction amount.")
    move_date = fields.Date(
        string='Transaction Date', related='move_id.date',
        help="Accounting date of the flagged journal entry.")
    move_ref = fields.Char(
        string='Reference', related='move_id.ref',
        help="Reference or memo of the flagged journal entry.")

    risk_color = fields.Integer(
        string='Risk Color', compute='_compute_risk_color', store=False,
        help="Numeric color index mapped to the risk level.")

    days_open = fields.Integer(
        string='Days Open', compute='_compute_days_open', store=False,
        help="Number of days this alert has remained open or under investigation.")

    # ─────────────────────────────────────────────────────────
    # Computed Methods
    # ─────────────────────────────────────────────────────────

    @api.depends('risk_level')
    def _compute_risk_color(self):
        """Compute numeric color index corresponding to the risk level for UI views."""
        color_map = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
        for rec in self:
            rec.risk_color = color_map.get(rec.risk_level, 4)

    @api.depends('alert_type')
    def _compute_type_icon(self):
        """Compute icon emoji character based on alert type."""
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
        """Compute number of days elapsed since the alert was detected if still open."""
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
        """Move alert state to 'Under Investigation' and assign current user."""
        self.ensure_one()
        self.write({
            'state': 'investigating',
            'assigned_to': self.env.user.id,
        })
        self.message_post(
            body=_("Alert moved to 'Under Investigation' by %s") % self.env.user.name)

    def action_resolve(self):
        """Mark alert as resolved with mandatory auditor resolution notes."""
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
        """Mark alert as a false positive after review."""
        self.ensure_one()
        self.write({
            'state': 'false_positive',
            'resolved_date': fields.Datetime.now(),
            'reviewed_by': self.env.user.id,
        })
        self.message_post(
            body=_("Marked as False Positive by %s") % self.env.user.name)

    def action_escalate(self):
        """Escalate alert for higher-level management review."""
        self.ensure_one()
        self.write({'state': 'escalated'})
        self.message_post(
            body=_("Alert escalated by %s") % self.env.user.name)

    def action_view_journal_entry(self):
        """Open the linked account.move record in form view."""
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
        """Assign the alert investigation to the current user."""
        self.write({'assigned_to': self.env.user.id})

    # ─────────────────────────────────────────────────────────
    # Batch Actions
    # ─────────────────────────────────────────────────────────

    def action_batch_resolve(self):
        """Bulk action to mark multiple selected alerts as resolved."""
        for rec in self:
            if rec.state not in ['resolved', 'false_positive']:
                rec.write({
                    'state': 'resolved',
                    'resolved_date': fields.Datetime.now(),
                    'reviewed_by': self.env.user.id,
                    'resolution_note': rec.resolution_note or 'Batch resolved',
                })

    def action_batch_false_positive(self):
        """Bulk action to mark multiple selected alerts as false positive."""
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
        """Validate that anomaly score remains within valid 0 to 100 range."""
        for rec in self:
            if not (0 <= rec.anomaly_score <= 100):
                raise UserError(_("Anomaly score must be between 0 and 100."))
