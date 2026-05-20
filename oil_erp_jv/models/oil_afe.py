# -*- coding: utf-8 -*-
#############################################################################
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

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class OilAFE(models.Model):
    """
    Authority for Expenditure — a budget approval document that JV partners
    vote on before the operator can proceed with a capital or operating
    expenditure. Contains line items for cost categories and tracks
    partner approvals.
    """
    _name = 'oil.afe'
    _description = 'Authority for Expenditure'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc, id desc'

    name = fields.Char(
        string='AFE Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help="Auto-generated AFE reference number.")
    title = fields.Char(
        string='AFE Title',
        required=True,
        tracking=True,
        help="Descriptive title for this expenditure authorization.")
    agreement_id = fields.Many2one(
        'oil.jv.agreement',
        string='JOA',
        required=True,
        tracking=True,
        domain="[('state', '=', 'active')]",
        help="The Joint Operating Agreement this AFE belongs to.")
    project_id = fields.Many2one(
        related='agreement_id.project_id',
        string='Project',
        store=True,
        help="Project from the linked JOA.")
    afe_type = fields.Selection(
        [
            ('capex', 'Capital Expenditure (CAPEX)'),
            ('opex', 'Operating Expenditure (OPEX)'),
        ],
        string='AFE Type',
        required=True,
        default='capex',
        tracking=True,
        help="Whether this is a capital or operating expenditure.")
    estimated_amount = fields.Monetary(
        string='Estimated Amount',
        currency_field='currency_id',
        required=True,
        tracking=True,
        help="Total estimated cost for this expenditure.")
    actual_amount = fields.Monetary(
        string='Actual Amount',
        currency_field='currency_id',
        compute='_compute_actual_amount',
        store=True,
        help="Total actual costs incurred against this AFE.")
    variance = fields.Monetary(
        string='Variance',
        currency_field='currency_id',
        compute='_compute_actual_amount',
        store=True,
        help="Difference between estimated and actual amounts.")
    currency_id = fields.Many2one(
        related='agreement_id.currency_id',
        store=True,
        help="Currency from the parent JOA.")
    company_id = fields.Many2one(
        related='agreement_id.company_id',
        store=True,
        help="Company from the parent JOA.")
    submission_date = fields.Date(
        string='Submission Date',
        default=fields.Date.today,
        tracking=True,
        help="Date the AFE was submitted for approval.")
    approval_date = fields.Date(
        string='Approval Date',
        tracking=True,
        help="Date the AFE was approved by JV partners.")
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted for Approval'),
            ('approved', 'Approved'),
            ('in_progress', 'In Progress'),
            ('closed', 'Closed'),
            ('rejected', 'Rejected'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        help="Current status of this AFE.")
    line_ids = fields.One2many(
        'oil.afe.line',
        'afe_id',
        string='Cost Estimate Lines',
        help="Breakdown of estimated costs by category.")
    approval_ids = fields.One2many(
        'oil.afe.approval',
        'afe_id',
        string='Partner Approvals',
        help="Approval votes from each JV partner.")
    total_estimated = fields.Monetary(
        string='Total Estimated',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help="Sum of all estimated line amounts.")
    description = fields.Text(
        string='Description',
        help="Detailed scope of work and justification.")
    notes = fields.Text(
        string='Notes',
        help="Additional notes.")
    expiry_warning = fields.Text(
        string='Expiry Warning',
        compute='_compute_expiry_warning',
        help="Warning if related JOA has expired.")

    def _compute_expiry_warning(self):
        """Shows warning if the JOA has expired."""
        for record in self:
            if (record.agreement_id
                    and record.agreement_id.state == 'expired'):
                record.expiry_warning = _(
                    "JV Agreement '%s' has expired.",
                    record.agreement_id.name)
            else:
                record.expiry_warning = False

    @api.depends('line_ids.estimated_amount')
    def _compute_totals(self):
        """Sums estimated amounts from all AFE lines."""
        for record in self:
            record.total_estimated = sum(
                record.line_ids.mapped('estimated_amount'))

    @api.depends('line_ids.actual_amount')
    def _compute_actual_amount(self):
        """Sums actual amounts and computes variance."""
        for record in self:
            record.actual_amount = sum(
                record.line_ids.mapped('actual_amount'))
            record.variance = record.estimated_amount - record.actual_amount

    @api.model_create_multi
    def create(self, vals_list):
        """Assigns auto-sequence on creation."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oil.afe') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        """Submits AFE for partner approval, auto-creates approval lines."""
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Only draft AFEs can be submitted."))
            if not record.line_ids:
                raise UserError(
                    _("Add at least one cost line before submitting."))
            # Auto-create approval lines for each JV partner
            existing_partners = record.approval_ids.mapped('partner_id')
            for jv_partner in record.agreement_id.partner_ids:
                if jv_partner.partner_id not in existing_partners:
                    self.env['oil.afe.approval'].create({
                        'afe_id': record.id,
                        'partner_id': jv_partner.partner_id.id,
                        'working_interest': jv_partner.working_interest,
                    })
            record.write({'state': 'submitted'})

    def action_approve(self):
        """Marks AFE as approved after checking partner votes."""
        for record in self:
            if record.state != 'submitted':
                raise UserError(
                    _("Only submitted AFEs can be approved."))
            # Check if sufficient WI% has approved (simple majority > 50%)
            approved_wi = sum(
                record.approval_ids.filtered(
                    lambda a: a.status == 'approved'
                ).mapped('working_interest'))
            if approved_wi < 50.0:
                raise UserError(
                    _("Insufficient approvals. Need >50%% WI approval. "
                      "Current: %.2f%%.", approved_wi))
            record.write({
                'state': 'approved',
                'approval_date': fields.Date.today(),
            })

    def action_start(self):
        """Moves AFE to in-progress status."""
        for record in self:
            if record.state != 'approved':
                raise UserError(
                    _("Only approved AFEs can be started."))
            record.write({'state': 'in_progress'})

    def action_close(self):
        """Closes the AFE."""
        for record in self:
            if record.state != 'in_progress':
                raise UserError(
                    _("Only in-progress AFEs can be closed."))
            record.write({'state': 'closed'})

    def action_reject(self):
        """Rejects the AFE."""
        for record in self:
            if record.state not in ('draft', 'submitted'):
                raise UserError(
                    _("Only draft or submitted AFEs can be rejected."))
            record.write({'state': 'rejected'})

    def action_set_to_draft(self):
        """Resets AFE back to draft."""
        for record in self:
            if record.state not in ('submitted', 'rejected'):
                raise UserError(
                    _("Only submitted or rejected AFEs can be reset to draft."))
            record.approval_ids.unlink()
            record.write({'state': 'draft'})


class OilAFELine(models.Model):
    """Individual cost line within an AFE."""
    _name = 'oil.afe.line'
    _description = 'AFE Cost Line'

    afe_id = fields.Many2one(
        'oil.afe',
        string='AFE',
        required=True,
        ondelete='cascade',
        help="The parent AFE.")
    currency_id = fields.Many2one(
        related='afe_id.currency_id',
        help="Currency from the parent AFE.")
    cost_category = fields.Selection(
        [
            ('drilling', 'Drilling'),
            ('completion', 'Completion'),
            ('facilities', 'Facilities'),
            ('pipeline', 'Pipeline'),
            ('environmental', 'Environmental'),
            ('geological', 'Geological & Geophysical'),
            ('labor', 'Labor'),
            ('materials', 'Materials & Equipment'),
            ('transportation', 'Transportation'),
            ('overhead', 'Overhead'),
            ('other', 'Other'),
        ],
        string='Cost Category',
        required=True,
        help="Category of the estimated cost.")
    description = fields.Char(
        string='Description',
        required=True,
        help="Description of this cost item.")
    estimated_amount = fields.Monetary(
        string='Estimated Amount',
        currency_field='currency_id',
        required=True,
        help="Estimated cost for this line item.")
    actual_amount = fields.Monetary(
        string='Actual Amount',
        currency_field='currency_id',
        help="Actual cost incurred for this line item.")
    account_id = fields.Many2one(
        'account.account',
        string='GL Account',
        help="General ledger account for this cost category.")

    @api.constrains('estimated_amount')
    def _check_estimated_amount(self):
        """Validates estimated amount is positive."""
        for line in self:
            if line.estimated_amount <= 0:
                raise ValidationError(
                    _("Estimated amount must be greater than zero."))


class OilAFEApproval(models.Model):
    """Tracks each JV partner's approval vote on an AFE."""
    _name = 'oil.afe.approval'
    _description = 'AFE Partner Approval'

    afe_id = fields.Many2one(
        'oil.afe',
        string='AFE',
        required=True,
        ondelete='cascade',
        help="The AFE being approved.")
    partner_id = fields.Many2one(
        'res.partner',
        string='JV Partner',
        required=True,
        help="The partner casting their vote.")
    working_interest = fields.Float(
        string='WI %',
        digits=(6, 4),
        help="Partner's working interest in this JOA.")
    status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Vote',
        default='pending',
        help="Partner's approval status for this AFE.")
    vote_date = fields.Date(
        string='Vote Date',
        help="Date when the partner cast their vote.")
    notes = fields.Text(
        string='Comments',
        help="Partner's comments on the AFE.")

    def action_vote_approve(self):
        """Partner approves the AFE."""
        for record in self:
            record.write({
                'status': 'approved',
                'vote_date': fields.Date.today(),
            })

    def action_vote_reject(self):
        """Partner rejects the AFE."""
        for record in self:
            record.write({
                'status': 'rejected',
                'vote_date': fields.Date.today(),
            })
