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
from odoo.exceptions import ValidationError


class OilInspectionOrder(models.Model):
    """
    Inspection Order — created when the user clicks 'Inspect' on a done MO.

    Each order contains:
    - A reference to the Manufacturing Order
    - A set of Pass/Fail + Remarks lines copied from the Inspection Point
    - An overall computed result (Pass / Fail / Pending)
    - A state machine: Draft → In Progress → Passed / Failed
    """
    _name = 'oil.inspection.order'
    _description = 'Oil Inspection Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help="Auto-generated unique reference for this inspection order.")
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('passed', 'Passed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help="Current workflow status of this inspection order.")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help="Select the company.")

    # ── MRP Link ──
    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        readonly=True,
        ondelete='cascade',
        help='The Manufacturing Order this inspection belongs to.',)
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        related='production_id.product_id',
        store=True,
        readonly=True,
        help="Select the product.")
    inspection_point_id = fields.Many2one(
        'oil.inspection.point',
        string='Inspection Point',
        readonly=True,
        help='The Inspection Point template this order was generated from.',)

    # ── People & Dates ──
    responsible_id = fields.Many2one(
        'res.users',
        string='Inspector',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        help="Select the inspector.")
    inspection_date = fields.Datetime(
        string='Inspection Date',
        default=fields.Datetime.now,
        required=True,
        help="Select the date and time for inspection Date.")

    # ── Checklist ──
    line_ids = fields.One2many(
        'oil.inspection.order.line',
        'order_id',
        string='Checklist',
        help="Individual checklist items to be evaluated during inspection.")

    # ── Computed Result ──
    result = fields.Selection(
        [
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('pending', 'Pending'),
        ],
        string='Result',
        compute='_compute_result',
        store=True,
        tracking=True,
        help="Overall inspection result computed from individual checklist items.")
    scrap_id = fields.Many2one(
        'stock.scrap',
        string='Scrap Movement',
        readonly=True,
        help="Scrap record created when the inspection fails.")
    note = fields.Html(string='Notes', help="Additional inspection notes and observations.")

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assigns a unique sequence number to new inspection order records.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oil.inspection.order') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids.result')
    def _compute_result(self):
        """
        Computes the overall inspection result based on the results of 
        individual checklist items, accounting for critical failures.
        """
        for rec in self:
            lines = rec.line_ids
            if not lines or any(not l.result for l in lines):
                rec.result = 'pending'
            elif any(l.result == 'fail' and l.is_critical for l in lines):
                rec.result = 'fail'
            elif all(l.result == 'pass' for l in lines):
                rec.result = 'pass'
            else:
                rec.result = 'fail'

    # ── State transitions ──
    def action_start(self):
        """
        Moves the inspection order from 'Draft' to 'In Progress'.
        """
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(
                    _('Only draft inspections can be started.'))
        self.write({'state': 'in_progress'})

    def action_pass(self):
        """
        Marks the inspection order as 'Passed' if all items are evaluated 
        and no critical items have failed.
        """
        for rec in self:
            if rec.state != 'in_progress':
                raise ValidationError(
                    _('Only in-progress inspections can be passed.'))
            unevaluated = rec.line_ids.filtered(lambda l: not l.result)
            if unevaluated:
                raise ValidationError(
                    _('All checklist items must be evaluated before passing.'))
            critical_fails = rec.line_ids.filtered(
                lambda l: l.result == 'fail' and l.is_critical)
            if critical_fails:
                raise ValidationError(
                    _('Inspection cannot be passed: critical item(s) have failed.'))
        self.write({'state': 'passed'})

    def action_fail(self):
        """
        Opens a wizard to confirm the failure and optionally scrap the product.
        """
        self.ensure_one()
        if self.state != 'in_progress':
            raise ValidationError(
                _('Only in-progress inspections can be failed.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Confirm Scrap & Fail'),
            'res_model': 'oil.inspection.fail.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_inspection_id': self.id},
        }

    def action_cancel(self):
        """
        Cancels the inspection order if it is not yet completed.
        """
        for rec in self:
            if rec.state in ('passed', 'failed'):
                raise ValidationError(
                    _('Completed inspections cannot be cancelled.'))
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        """
        Resets a cancelled inspection order back to 'Draft' state.
        """
        for rec in self:
            if rec.state != 'cancelled':
                raise ValidationError(
                    _('Only cancelled inspections can be reset.'))
        self.write({'state': 'draft'})


class OilInspectionOrderLine(models.Model):
    """A single checklist item within an Inspection Order."""
    _name = 'oil.inspection.order.line'
    _description = 'Oil Inspection Order Line'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10, help="Order of this item in the checklist.")
    order_id = fields.Many2one(
        'oil.inspection.order',
        string='Inspection Order',
        required=True,
        ondelete='cascade',
        help="Parent inspection order this item belongs to.")
    name = fields.Char(
        string='Check Item',
        required=True,
        help="Description of the quality check to perform.")
    guideline = fields.Text(
        string='Guideline',
        readonly=True,
        help="Instructions for the inspector on how to evaluate this item.")
    is_critical = fields.Boolean(
        string='Critical',
        default=False,
        help="If checked, a failure on this item automatically fails the entire inspection.")
    result = fields.Selection(
        [('pass', 'Pass'),('fail', 'Fail'),
        ],
        string='Result',
        help="Choose the result.")
    percentage = fields.Float(
        string='Percentage (%)',
        digits=(5, 2),
        help="Measured percentage value for threshold-based evaluation.")
    evaluation_type = fields.Selection(
        [('manual', 'Pass/Fail'), ('percentage', 'Percentage')],
        string='Evaluation Type',
        help="Whether this item is evaluated manually or by percentage.")
    target_value = fields.Float(
        string='Target Value (%)',
        help="Minimum percentage threshold required to pass.")
    remarks = fields.Text(
        string='Remarks',
        help="Inspector notes explaining the evaluation result.")

    @api.onchange('percentage', 'evaluation_type', 'target_value')
    def _onchange_percentage(self):
        """
        Auto-computes the result of a line item based on the entered percentage 
        compared to the target value.
        """
        for rec in self:
            if rec.evaluation_type == 'percentage':
                if rec.percentage < rec.target_value:
                    rec.result = 'fail'
                else:
                    rec.result = 'pass'

    @api.constrains('result', 'remarks')
    def _check_fail_remarks(self):
        """
        Ensure remarks are provided when result is set to 'fail'.
        """
        for rec in self:
            if rec.result == 'fail' and not rec.remarks:
                raise ValidationError(
                    _('Remarks are required for items marked as Fail.'))
