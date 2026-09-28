# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Abhijith CK(odoo@cybrosys.com)
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


class HrEmployee(models.Model):
    """This class inherits from 'hr.employee' and
     extends it with additional fields and methods.
    """
    _inherit = 'hr.employee'

    entry_checklist_ids = fields.Many2many('employee.checklist',
                                           'entry_obj_ids', 'check_hr_rel',
                                           'hr_check_rel',
                                           help="checklists to enable entry process",
                                           string='Entry Process',
                                           domain=[
                                               ('document_type', '=', 'entry')])
    exit_checklist_ids = fields.Many2many('employee.checklist', 'exit_obj_ids',
                                          'exit_hr_rel', 'hr_exit_rel',
                                          help="checklists to enable exit process",
                                          string='Exit Process',
                                          domain=[
                                              ('document_type', '=', 'exit')])
    entry_progress = fields.Float(help='Entry progress percentage of employee', compute="_compute_entry_progress",
                                  string='Entry Progress', store=True,
                                  default=0.0)
    exit_progress = fields.Float(help='Exit progress percentage of employee',
                                 compute='_compute_exit_progress', string='Exit Progress',
                                 store=True, default=0.0)
    maximum_rate = fields.Integer(help="Maximum rate of the progress percentage", default=100)
    check_list_enable = fields.Boolean(help='Is check list enable',
                                       copy=False)

    @api.depends('exit_checklist_ids')
    def _compute_exit_progress(self):
        """Calculate the exit progress for an employee."""

        for each in self:
            total_len = self.env['employee.checklist'].search_count(
                [('document_type', '=', 'exit')])
            entry_len = len(each.exit_checklist_ids)
            if total_len != 0:
                each.exit_progress = round((entry_len * 100) / total_len, 2)

    @api.depends('entry_checklist_ids')
    def _compute_entry_progress(self):
        """Calculate the entry progress for an employee."""

        for each in self:
            total_len = self.env['employee.checklist'].search_count(
                [('document_type', '=', 'entry')])
            entry_len = len(each.entry_checklist_ids)
            if total_len != 0:
                each.entry_progress = round((entry_len * 100) / total_len, 2)


class HrEmployeeDocument(models.Model):
    """This class inherits from 'hr.employee.document' and adds custom logic
         for document creation and deletion."""
    _inherit = 'hr.employee.document'

    @api.model
    def create(self, vals):
        """Create a new employee document and update the associated checklists."""
        result = super(HrEmployeeDocument, self).create(vals)
        if result.document_id.document_type == 'entry':
            result.employee_id.write(
                {'entry_checklist_ids': [(4, result.document_id.id)]})
        if result.document_id.document_type == 'exit':
            result.employee_id.write(
                {'exit_checklist_ids': [(4, result.document_id.id)]})
        return result

    def unlink(self):
        """ Delete an employee document and update the associated checklists."""
        for result in self:
            if result.document_id.document_type == 'entry':
                result.employee_id.write(
                    {'entry_checklist_ids': [(5, result.document_id.id)]})
            if result.document_id.document_type == 'exit':
                result.employee_id.write(
                    {'exit_checklist_ids': [(5, result.document_id.id)]})
        res = super(HrEmployeeDocument, self).unlink()
        return res


class EmployeeChecklist(models.Model):
    """This class inherits from 'employee.checklist' and extends it with
         invisible fields."""
    _inherit = 'employee.checklist'

    entry_obj_ids = fields.Many2many('hr.employee', 'entry_checklist_ids',
                                     'hr_check_rel', 'check_hr_rel', )
    exit_obj_ids = fields.Many2many('hr.employee', 'exit_checklist_ids',
                                    'hr_exit_rel', 'exit_hr_rel', )
