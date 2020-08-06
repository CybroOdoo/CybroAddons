# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import date
from odoo import models, fields, api

emp_stages = [('joined', 'Slap On'),
              ('grounding', 'Grounding'),
              ('test_period', 'Test Period'),
              ('employment', 'Employment'),
              ('notice_period', 'Notice Period'),
              ('relieved', 'Resigned'),
              ('terminate', 'Terminated')]


class EmployeeFormInherit(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def create(self, vals):
        result = super(EmployeeFormInherit, self).create(vals)
        result.stages_history.sudo().create({'start_date': date.today(),
                                             'employee_id': result.id,
                                             'state': 'joined'})
        return result

    @api.multi
    def start_grounding(self):
        self.state = 'grounding'
        self.stages_history.sudo().create({'start_date': date.today(),
                                           'employee_id': self.id,
                                           'state': 'grounding'})

    @api.multi
    def set_as_employee(self):
        self.state = 'employment'
        stage_obj = self.stages_history.search([('employee_id', '=', self.id),
                                                ('state', '=', 'test_period')])
        if stage_obj:
            stage_obj.sudo().write({'end_date': date.today()})
        self.stages_history.sudo().create({'start_date': date.today(),
                                           'employee_id': self.id,
                                           'state': 'employment'})

    @api.multi
    def start_notice_period(self):
        self.state = 'notice_period'
        stage_obj = self.stages_history.search([('employee_id', '=', self.id),
                                                ('state', '=', 'employment')])
        if stage_obj:
            stage_obj.sudo().write({'end_date': date.today()})
        self.stages_history.sudo().create({'start_date': date.today(),
                                           'employee_id': self.id,
                                           'state': 'notice_period'})

    @api.multi
    def relived(self):
        self.state = 'relieved'
        self.active = False
        stage_obj = self.stages_history.search([('employee_id', '=', self.id),
                                                ('state', '=', 'notice_period')])
        if stage_obj:
            stage_obj.sudo().write({'end_date': date.today()})
        self.stages_history.sudo().create({'end_date': date.today(),
                                           'employee_id': self.id,
                                           'state': 'relieved'})

    @api.multi
    def start_test_period(self):
        self.state = 'test_period'
        self.stages_history.search([('employee_id', '=', self.id),
                                    ('state', '=', 'grounding')]).sudo().write({'end_date': date.today()})
        self.stages_history.sudo().create({'start_date': date.today(),
                                           'employee_id': self.id,
                                           'state': 'test_period'})

    @api.multi
    def terminate(self):
        self.state = 'terminate'
        self.active = False
        stage_obj = self.stages_history.search([('employee_id', '=', self.id),
                                                ('state', '=', 'employment')])

        if stage_obj:
            stage_obj.sudo().write({'end_date': date.today()})
        else:
            self.stages_history.search([('employee_id', '=', self.id),
                                        ('state', '=', 'grounding')]).sudo().write({'end_date': date.today()})
        self.stages_history.sudo().create({'end_date': date.today(),
                                           'employee_id': self.id,
                                           'state': 'terminate'})

    state = fields.Selection(emp_stages, string='Status', default='joined', track_visibility='always', copy=False,
                             help="Employee Stages.\nSlap On: Joined\nGrounding: Training\nTest period : Probation")
    stages_history = fields.One2many('hr.employee.status.history', 'employee_id', string='Stage History',
                                     help='It shows the duration and history of each stages')


class EmployeeStageHistory(models.Model):
    _name = 'hr.employee.status.history'
    _description = 'Status History'

    @api.depends('end_date')
    def get_duration(self):
        for each in self:
            if each.end_date and each.start_date:
                duration = fields.Date.from_string(each.end_date) - fields.Date.from_string(each.start_date)
                each.duration = duration.days

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    duration = fields.Integer(compute=get_duration, string='Duration(days)')
    state = fields.Selection(emp_stages, string='Stage')
    employee_id = fields.Many2one('hr.employee', invisible=1)


class WizardEmployee(models.TransientModel):
    _name = 'wizard.employee.stage'

    @api.multi
    def set_as_employee(self):
        context = self._context
        employee_obj = self.env['hr.employee'].search([('id', '=', context.get('employee_id'))])
        if self.related_user:
            employee_obj.user_id = self.related_user
        employee_obj.set_as_employee()

    related_user = fields.Many2one('res.users', string="Related User")

