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


class OilHsePermit(models.Model):
    """
    Model for managing HSE Work Permits (e.g., Hot Work, Confined Space).
    Controls task transitions that require valid permits before proceeding.
    """
    _name = 'oil.hse.permit'
    _description = 'HSE Work Permit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Auto-generated reference for the work permit.',
    )
    permit_type = fields.Selection(
        [
            ('hot_work', 'Hot Work'),
            ('cold_work', 'Cold Work'),
            ('confined_space', 'Confined Space'),
            ('electrical', 'Electrical'),
        ],
        string='Permit Type',
        required=True,
        tracking=True,
        help='Type of permit required for the planned activity.',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help="Select the company.")

    start_date = fields.Datetime(
        string='Start Date',
        required=True,
        tracking=True,
        help='Date and time when the permit becomes active.',)
    end_date = fields.Datetime(
        string='End Date',
        required=True,
        tracking=True,
        help='Date and time when the permit expires.',)

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        domain=[('is_oil_gas_project', '=', True)],
        help='Project covered by the permit.',)
    task_id = fields.Many2one(
        'project.task',
        string='Well / Task',
        domain=[('project_id.is_oil_gas_project', '=', True)],
        help='Specific well or task covered by the permit.',)

    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        help='User who approved the permit.',)
    from_stage_id = fields.Many2one(
        'project.task.type',
        string='From Stage',
        readonly=True,
        help='Stage the task was in before being moved to Waiting for a permit.',)
    to_stage_id = fields.Many2one(
        'project.task.type',
        string='To Stage',
        readonly=True,
        help='Target stage requiring a permit.',)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('expired', 'Expired'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        help='Current approval status of the permit.',)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """
        Validates that the permit end date is after the start date.
        """
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date <= rec.start_date:
                raise ValidationError(
                    _('Permit end date must be later than the start date.'))

    @api.constrains('project_id', 'task_id')
    def _check_task_project(self):
        """
        Ensures that the selected well or task belongs strictly to the chosen project.
        """
        for rec in self:
            if rec.project_id and rec.task_id and rec.task_id.project_id != rec.project_id:
                raise ValidationError(
                    _('Selected well/task must belong to the chosen project.'))

    @api.model_create_multi
    def create(self, vals_list):
        """Overrides create to assign a unique work permit reference sequence."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oil.hse.permit') or _('New')
        return super().create(vals_list)

    def action_approve(self):
        """
        Approves the permit, records the approver, and potentially moves the
        linked task out of the 'Waiting for Permit' stage if conditions are met.
        """
        waiting_stage = self.env['project.task.type'].search(
            [('is_waiting_stage', '=', True)], limit=1
        )
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('Only draft permits can be approved.'))
        self.write({
            'state': 'approved',
            'approved_by': self.env.uid,
        })
        for rec in self:
            if rec.task_id and rec.to_stage_id:
                if rec.task_id.stage_id == waiting_stage:
                    rec.task_id.with_context(
                        skip_work_permit_stage_check=True).write({
                        'stage_id': rec.to_stage_id.id,
                        'prev_stage_id': False,
                        'requested_stage_id': False,
                    })

    def action_expire(self):
        """
        Marks an approved permit as expired once its validity duration has passed.
        """
        for rec in self:
            if rec.state != 'approved':
                raise ValidationError(
                    _('Only approved permits can be marked as expired.'))
        self.write({'state': 'expired'})

    def action_cancel(self):
        """Cancels a work permit, rendering it invalid for task transitions."""
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        """Resets an expired or cancelled permit back to draft for re-evaluation."""

        self.write({'state': 'draft', 'approved_by': False})
