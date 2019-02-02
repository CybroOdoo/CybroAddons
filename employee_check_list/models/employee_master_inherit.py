# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, fields, api


class EmployeeMasterInherit(models.Model):
    _inherit = 'hr.employee'

    @api.depends('exit_checklist')
    def exit_progress(self):
        for each in self:
            total_len = self.env['employee.checklist'].search_count([('document_type', '=', 'exit')])
            entry_len = len(each.exit_checklist)
            if total_len != 0:
                each.exit_progress = (entry_len * 100) / total_len

    @api.depends('entry_checklist')
    def entry_progress(self):
        for each in self:
            total_len = self.env['employee.checklist'].search_count([('document_type', '=', 'entry')])
            entry_len = len(each.entry_checklist)
            if total_len != 0:
                each.entry_progress = (entry_len*100) / total_len

    entry_checklist = fields.Many2many('employee.checklist', 'entry_obj', 'check_hr_rel', 'hr_check_rel',
                                       string='Entry Process',
                                       domain=[('document_type', '=', 'entry')])
    exit_checklist = fields.Many2many('employee.checklist', 'exit_obj', 'exit_hr_rel', 'hr_exit_rel',
                                      string='Exit Process',
                                      domain=[('document_type', '=', 'exit')])
    entry_progress = fields.Float(compute=entry_progress, string='Entry Progress', store=True, default=0.0)
    exit_progress = fields.Float(compute=exit_progress, string='Exit Progress', store=True, default=0.0)
    maximum_rate = fields.Integer(default=100)
    check_list_enable = fields.Boolean(invisible=True, copy=False)


class EmployeeDocumentInherit(models.Model):
    _inherit = 'hr.employee.document'

    @api.model
    def create(self, vals):
        result = super(EmployeeDocumentInherit, self).create(vals)
        if result.document_name.document_type == 'entry':
            result.employee_ref.write({'entry_checklist': [(4, result.document_name.id)]})
        if result.document_name.document_type == 'exit':
            result.employee_ref.write({'exit_checklist': [(4, result.document_name.id)]})
        return result

    @api.multi
    def unlink(self):
        for result in self:
            if result.document_name.document_type == 'entry':
                result.employee_ref.write({'entry_checklist': [(5, result.document_name.id)]})
            if result.document_name.document_type == 'exit':
                result.employee_ref.write({'exit_checklist': [(5, result.document_name.id)]})
        res = super(EmployeeDocumentInherit, self).unlink()
        return res


class EmployeeChecklistInherit(models.Model):
    _inherit = 'employee.checklist'

    entry_obj = fields.Many2many('hr.employee', 'entry_checklist', 'hr_check_rel', 'check_hr_rel',
                                 invisible=1)
    exit_obj = fields.Many2many('hr.employee', 'exit_checklist', 'hr_exit_rel', 'exit_hr_rel',
                                invisible=1)
