# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields, api


class EmployeeMasterInherit(models.Model):
    _inherit = 'hr.employee'

    @api.depends('exit_checklist_ids')
    def exit_progress(self):
        for each in self:
            total_len = self.env['employee.checklist'].search_count([('document_type', '=', 'exit')])
            entry_len = len(each.exit_checklist_ids)
            if total_len != 0:
                each.exit_progress = (entry_len * 100) / total_len

    @api.depends('entry_checklist_ids')
    def entry_progress(self):
        for each in self:
            total_len = self.env['employee.checklist'].search_count([('document_type', '=', 'entry')])
            entry_len = len(each.entry_checklist_ids)
            if total_len != 0:
                each.entry_progress = (entry_len*100) / total_len

    entry_checklist_ids = fields.Many2many('employee.checklist', 'entry_obj_ids', 'check_hr_rel', 'hr_check_rel',
                                       string='Entry Process',
                                       domain=[('document_type', '=', 'entry')])
    exit_checklist_ids = fields.Many2many('employee.checklist', 'exit_obj_ids', 'exit_hr_rel', 'hr_exit_rel',
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
            result.employee_ref.write({'entry_checklist_ids': [(4, result.document_name.id)]})
        if result.document_name.document_type == 'exit':
            result.employee_ref.write({'exit_checklist_ids': [(4, result.document_name.id)]})
        return result

    def unlink(self):
        for result in self:
            if result.document_name.document_type == 'entry':
                result.employee_ref.write({'entry_checklist_ids': [(5, result.document_name.id)]})
            if result.document_name.document_type == 'exit':
                result.employee_ref.write({'exit_checklist_ids': [(5, result.document_name.id)]})
        res = super(EmployeeDocumentInherit, self).unlink()
        return res


class EmployeeChecklistInherit(models.Model):
    _inherit = 'employee.checklist'

    entry_obj_ids = fields.Many2many('hr.employee', 'entry_checklist_ids', 'hr_check_rel', 'check_hr_rel',
                                 invisible=1)
    exit_obj_ids = fields.Many2many('hr.employee', 'exit_checklist_ids', 'hr_exit_rel', 'exit_hr_rel',
                                invisible=1)
