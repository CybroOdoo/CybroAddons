# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DisciplinaryAction(models.Model):
    """Model representing an action for disciplinary"""
    _name = 'disciplinary.action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Disciplinary Action"

    # Assigning the sequence for the record
    @api.model
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code(
                'disciplinary.action')
        return super(DisciplinaryAction, self).create(vals)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('explain', 'Waiting Explanation'),
        ('submitted', 'Waiting Action'),
        ('action', 'Action Validated'),
        ('cancel', 'Cancelled'),
    ], default='draft', track_visibility='onchange',
        help="Stage for disciplinary action")
    name = fields.Char(string='Reference', copy=False,
                       readonly=True,
                       default=lambda self: _('New'),
                       help="Name for disciplinary action")
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                    required=True, help="Employee name")
    department_id = fields.Many2one('hr.department', string='Department',
                                      required=True, help="Department name")
    discipline_reason_id = fields.Many2one('discipline.category', string='Reason',
                                        required=True,
                                        help="Choose a disciplinary reason")
    explanation = fields.Text(string="Explanation by Employee",
                              help='Employee have to give Explanation'
                                   'to manager about the violation of discipline')
    action_id = fields.Many2one('discipline.category', string="Action",
                             help="Choose an action for this disciplinary action")
    read_only = fields.Boolean(compute="_compute_get_user", default=True,
                               help="Boolean field for get the user")
    warning_letter = fields.Html(string="Warning Letter",
                                 help="Warning letter as disciplinary action")
    suspension_letter = fields.Html(string="Suspension Letter",
                                    help="Suspension letter as disciplinary action")
    termination_letter = fields.Html(string="Termination Letter",
                                     help="Termination letter as disciplinary action")
    warning = fields.Boolean(string='Warning', default=False,
                             help='Boolean field for to show the message as warning message')
    action_details = fields.Text(string="Action Details",
                                 help="Give the details for this action")
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments",
                                      help="Employee can submit any documents which supports their explanation")
    note = fields.Text(string="Internal Note",
                       help='Internal notes regarding the disciplinary action')
    joined_date = fields.Date(string="Joined Date",
                              help="Employee joining date")


    # Check the user is a manager or employee
    @api.depends_context('uid')
    def _compute_get_user(self):
        """Method for getting the user from the groups"""
        if self.env.user.has_group('hr.group_hr_manager'):
            self.read_only = True
        else:
            self.read_only = False

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """On change function for the employee name and based on the
         value it updated the department"""
        employee = self.env['hr.employee'].search(
            [('name', '=', self.employee_id.name)])
        self.department_id = employee.department_id.id
        if self.state == 'action':
            raise ValidationError(_('You Can not edit a Validated Action !!'))

    @api.onchange('discipline_reason_id')
    def _onchange_discipline_reason_id(self):
        """On change function for the discipline reason and that check the
         state and raise a validation error"""
        if self.state == 'action':
            raise ValidationError(_('You Can not edit a Validated Action !!'))

    def assign_function(self):
        """Method to update state"""
        for rec in self:
            rec.state = 'explain'

    def cancel_function(self):
        """Cancel function for the discipline reason"""
        for rec in self:
            rec.state = 'cancel'

    def set_to_function(self):
        """State set to draft state"""
        for rec in self:
            rec.state = 'draft'

    def action_function(self):
        """Method used for raise validation based on the actions"""
        for rec in self:
            if not rec.action_id:
                raise ValidationError(_('You have to select an Action !!'))
            if not rec.action_details or rec.action_details == '<p><br></p>':
                raise ValidationError(
                    _('You have to fill up the Action Details in Action Information !!'))
            rec.state = 'action'

    def explanation_function(self):
        """Method used for raise validation based on the explanation"""
        for rec in self:
            if not rec.explanation:
                raise ValidationError(_('You must give an explanation !!'))
        self.write({
            'state': 'submitted'
        })
