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
from odoo import api, fields, models


class HrEmployee(models.Model):
    """This is used to inherit the employee model"""
    _inherit = 'hr.employee'

    state = fields.Selection([('joined', 'Slap On'),
                              ('grounding', 'Grounding'),
                              ('test_period', 'Test Period'),
                              ('employment', 'Employment'),
                              ('notice_period', 'Notice Period'),
                              ('relieved', 'Resigned'),
                              ('terminate', 'Terminated')], string='Status',
                             default='joined',
                             tracking=True, copy=False,
                             help="Employee Stages.\nSlap On: "
                                  "Joined\nGrounding: Training\nTest Period: "
                                  "Probation")
    stages_history_ids = fields.One2many('hr.employee.status.history',
                                         'employee_id', string='Stage History',
                                         help='It shows the duration and '
                                              'history of employee stages')

    @api.model_create_multi
    def create(self, vals_list):
        """This is used to create the default stage as 'Slap On'"""
        employees = super().create(vals_list)
        history_vals = [
            {
                'start_date': fields.Date.today(),
                'employee_id': employee.id,
                'state': employee.state or 'joined',
            }
            for employee in employees
        ]
        self.env['hr.employee.status.history'].sudo().create(history_vals)
        return employees

    def action_start_grounding(self):
        """This is used to create the ground stage on staging history"""
        for employee in self:
            employee.state = 'grounding'
            stage_history_ids = self.env['hr.employee.status.history'].search(
                [('employee_id', '=', employee.id),
                 ('state', '=', 'joined'),
                 ('end_date', '=', False)])
            if stage_history_ids:
                stage_history_ids.sudo().write({'end_date': fields.Date.today()})
            employee.stages_history_ids.sudo().create({
                'start_date': fields.Date.today(),
                'employee_id': employee.id,
                'state': 'grounding',
            })

    def set_as_employee(self):
        """This is used to create the employee stage on staging history"""
        for employee in self:
            employee.state = 'employment'
            stage_history_ids = self.env['hr.employee.status.history'].search(
                [('employee_id', '=', employee.id),
                 ('state', 'in', ('test_period', 'joined')),
                 ('end_date', '=', False)])
            if stage_history_ids:
                stage_history_ids.sudo().write({'end_date': fields.Date.today()})
            employee.stages_history_ids.sudo().create({
                'start_date': fields.Date.today(),
                'employee_id': employee.id,
                'state': 'employment',
            })

    def action_start_notice_period(self):
        """This is used to create the notice period stage on staging history"""
        for employee in self:
            employee.state = 'notice_period'
            stage_history_ids = self.env['hr.employee.status.history'].search(
                [('employee_id', '=', employee.id),
                 ('state', '=', 'employment'),
                 ('end_date', '=', False)])
            if stage_history_ids:
                stage_history_ids.sudo().write({'end_date': fields.Date.today()})
            employee.stages_history_ids.sudo().create({
                'start_date': fields.Date.today(),
                'employee_id': employee.id,
                'state': 'notice_period',
            })

    def action_relived(self):
        """This is used to create the relieved stage on staging history"""
        for employee in self:
            employee.state = 'relieved'
            employee.active = False
            stage_history_ids = self.env['hr.employee.status.history'].search(
                [('employee_id', '=', employee.id),
                  ('state', '=', 'notice_period'),
                  ('end_date', '=', False)])
            if stage_history_ids:
                stage_history_ids.sudo().write({'end_date': fields.Date.today()})
            employee.stages_history_ids.sudo().create({
                'start_date': fields.Date.today(),
                'end_date': fields.Date.today(),
                'employee_id': employee.id,
                'state': 'relieved',
            })

    def action_start_test_period(self):
        """This is used to create the test period stage on staging history"""
        for employee in self:
            employee.state = 'test_period'
            stage_history_ids = self.env['hr.employee.status.history'].search(
                [('employee_id', '=', employee.id),
                 ('state', '=', 'grounding'),
                 ('end_date', '=', False)])
            if stage_history_ids:
                stage_history_ids.sudo().write({'end_date': fields.Date.today()})
            employee.stages_history_ids.sudo().create({
                'start_date': fields.Date.today(),
                'employee_id': employee.id,
                'state': 'test_period',
            })

    def action_terminate(self):
        """This is used to create the terminate stage on staging history"""
        for employee in self:
            employee.state = 'terminate'
            employee.active = False
            stage_history_ids = self.env['hr.employee.status.history'].search(
                [('employee_id', '=', employee.id),
                 ('state', 'in', ('employment', 'grounding', 'test_period', 'notice_period', 'joined')),
                 ('end_date', '=', False)])
            if stage_history_ids:
                stage_history_ids.sudo().write({'end_date': fields.Date.today()})
            employee.stages_history_ids.sudo().create({
                'start_date': fields.Date.today(),
                'end_date': fields.Date.today(),
                'employee_id': employee.id,
                'state': 'terminate',
            })


class EmployeeStageHistory(models.Model):
    """This is used to show the employee stages history"""
    _name = 'hr.employee.status.history'
    _description = 'Status History'
    _order = 'start_date desc, id desc'

    start_date = fields.Date(help="Start date of the status period")
    end_date = fields.Date(help="End date of the status period")
    duration = fields.Integer(compute='_compute_get_duration',
                              string='Duration (days)',
                              help="Duration of the stage")
    state = fields.Selection([('joined', 'Slap On'),
                              ('grounding', 'Grounding'),
                              ('test_period', 'Test Period'),
                              ('employment', 'Employment'),
                              ('notice_period', 'Notice Period'),
                              ('relieved', 'Resigned'),
                              ('terminate', 'Terminated')], string='Stage')
    employee_id = fields.Many2one('hr.employee', ondelete='cascade',
                                  help="Stage of the employee")

    @api.depends('start_date', 'end_date')
    def _compute_get_duration(self):
        """This is used to calculate the duration for the stages"""
        for history in self:
            if history.end_date and history.start_date:
                history.duration = (history.end_date - history.start_date).days
            else:
                history.duration = 0
