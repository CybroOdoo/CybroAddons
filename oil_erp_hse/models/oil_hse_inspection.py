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


class OilHseInspection(models.Model):
    """
    Model for recording Health, Safety, and Environment (HSE) inspections.
    Tracks inspection types, inspectors, associated projects/tasks,
    and detailed checklist findings.
    """
    _name = 'oil.hse.inspection'
    _description = 'HSE Inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Auto-generated reference for the inspection.',
    )
    date = fields.Date(
        string='Inspection Date',
        default=fields.Date.today,
        required=True,
        tracking=True,
        help='Date when the inspection was performed.',
    )
    inspection_type = fields.Selection(
        [
            ('safety', 'Safety'),
            ('environment', 'Environment'),
            ('equipment', 'Equipment'),
        ],
        string='Inspection Type',
        required=True,
        tracking=True,
        help='Type of inspection being carried out.',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help="Select the company.")

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        domain=[('is_oil_gas_project', '=', True)],
        help='Project associated with the inspection.',)
    task_id = fields.Many2one(
        'project.task',
        string='Well / Task',
        domain=[('project_id.is_oil_gas_project', '=', True)],
        help='Specific well or task inspected.',)
    inspector_id = fields.Many2one(
        'res.users',
        string='Inspector',
        default=lambda self: self.env.user,
        required=True,
        help='User responsible for carrying out the inspection.',)
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Equipment',
        help='Equipment to be inspected.',)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('done', 'Done'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help="Choose the status.")
    checklist_line_ids = fields.One2many(
        'oil.hse.checklist.line',
        'inspection_id',
        string='Checklist',
        help='Detailed inspection checklist lines and findings.')

    @api.constrains('date')
    def _check_date(self):
        """
        Validates that the inspection date is not in the future.
        """
        today = fields.Date.today()
        for rec in self:
            if rec.date and rec.date > today:
                raise ValidationError(
                    _('Inspection date cannot be in the future.'))

    @api.constrains('project_id', 'task_id')
    def _check_task_project(self):
        """
        Ensures that the selected well/task belongs to the assigned project.
        """
        for rec in self:
            if rec.project_id and rec.task_id and rec.task_id.project_id != rec.project_id:
                raise ValidationError(
                    _('Selected well/task must belong to the chosen project.'))

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assigns a unique sequence number to new inspection records.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oil.hse.inspection') or _('New')
        return super().create(vals_list)


class OilHseChecklistLine(models.Model):
    """
    Represents an individual item within an HSE inspection checklist.
    """
    _name = 'oil.hse.checklist.line'
    _description = 'HSE Checklist Line'

    inspection_id = fields.Many2one(
        'oil.hse.inspection',
        string='Inspection',
        required=True,
        ondelete='cascade',
        help='Inspection record that this checklist item belongs to.',
    )
    name = fields.Char(
        string='Check Item',
        required=True,
        help='Specific item or control point being inspected.',
    )
    status = fields.Selection(
        [
            ('ok', 'OK'),
            ('not_ok', 'Not OK'),
        ],
        string='Status',
        required=True,
        help='Inspection result for this checklist item.',
    )
    remarks = fields.Text(
        string='Remarks',
        help='Notes, observations, or corrective comments for this line.',
    )

    @api.constrains('status', 'remarks')
    def _check_not_ok_remarks(self):
        """
        Forces the user to provide remarks if a checklist item is marked as 'Not OK'.
        """
        for rec in self:
            if rec.status == 'not_ok' and not rec.remarks:
                raise ValidationError(
                    _('Add remarks for checklist items marked as Not OK.'))
