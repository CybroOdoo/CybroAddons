# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
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
from openerp.report import report_sxw
from openerp.osv import osv
from openerp.http import request


class ProjectReportParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(ProjectReportParser, self).__init__(cr, uid, name, context=context)

        self.localcontext.update({
            'get_task_model': self.get_task_model,
            'get_issue_model': self.get_issue_model,
            'get_list_model_task': self.get_list_model_task,
            'get_list_model_issue': self.get_list_model_issue,

        })
        self.context = context

    def get_task_model(self, name):
        wizard_record = request.env['wizard.project.report'].search([])[-1]
        task_obj = request.env['project.task']
        users_selected = []
        stages_selected = []
        for elements in wizard_record.partner_select:
            users_selected.append(elements.id)
        for elements in wizard_record.stage_select:
            stages_selected.append(elements.id)
        if len(wizard_record.partner_select) == 0:
            if len(wizard_record.stage_select) == 0:
                current_task_obj = task_obj.search([('project_id', '=', name)])
                return current_task_obj
            else:
                current_task_obj = task_obj.search([('project_id', '=', name), ('stage_id', 'in', stages_selected)])
                return current_task_obj
        else:
            if len(wizard_record.stage_select) == 0:
                current_task_obj = task_obj.search([('project_id', '=', name), ('user_id', 'in', users_selected)])
                return current_task_obj
            else:
                current_task_obj = task_obj.search(
                    [('project_id', '=', name), ('user_id', 'in', users_selected), ('stage_id', 'in', stages_selected)])
                return current_task_obj

    def get_issue_model(self, name):
        wizard_record = request.env['wizard.project.report'].search([])[-1]
        issue_obj = request.env['project.issue']
        task_obj = issue_obj
        users_selected = []
        stages_selected = []
        for elements in wizard_record.partner_select:
            users_selected.append(elements.id)
        for elements in wizard_record.stage_select:
            stages_selected.append(elements.id)
        if len(wizard_record.partner_select) == 0:
            if len(wizard_record.stage_select) == 0:
                current_task_obj = task_obj.search([('project_id', '=', name)])
                return current_task_obj
            else:
                current_task_obj = task_obj.search([('project_id', '=', name), ('stage_id', 'in', stages_selected)])
                return current_task_obj
        else:
            if len(wizard_record.stage_select) == 0:
                current_task_obj = task_obj.search([('project_id', '=', name), ('user_id', 'in', users_selected)])
                return current_task_obj
            else:
                current_task_obj = task_obj.search(
                    [('project_id', '=', name), ('user_id', 'in', users_selected), ('stage_id', 'in', stages_selected)])
                return current_task_obj

    def get_list_model_task(self, name):
        wizard_record = request.env['wizard.project.report'].search([])[-1]
        if wizard_record.task_select == True:
            return 2
        else:
            return 3
    def get_list_model_issue(self, name):
        wizard_record = request.env['wizard.project.report'].search([])[-1]
        if wizard_record.issue_select == True:
            return 2
        else:
            return 3


class PrintReportProject(osv.AbstractModel):

    _name = 'report.project_report_pdf.project_report_transition'
    _inherit = 'report.abstract_report'
    _template = 'project_report_pdf.project_report_transition'
    _wrapped_report_class = ProjectReportParser


