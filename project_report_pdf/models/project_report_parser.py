# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nilmar Shereef(<https://www.cybrosys.com>)
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

from odoo.http import request
from odoo import models, api


class ProjectReportParser(models.AbstractModel):
    _name = 'report.project_report_pdf.project_report_template'

    def get_task_model(self, name):
        wizard_record = request.env['wizard.project.report'].search([])[-1]
        task_obj = request.env['project.task']
        users_selected = []
        stages_selected = []
        current_task_obj = []
        for elements in wizard_record.partner_select:
            users_selected.append(elements.id)
        for elements in wizard_record.stage_select:
            stages_selected.append(elements.id)
        if len(wizard_record.partner_select) == 0:
            if len(wizard_record.stage_select) == 0:
                current_task = task_obj.search([('project_id', '=', name)])
                for i in current_task:
                    vals = {
                        'name': i.name,
                        'user_id': i.user_id.name,
                        'stage_id': i.stage_id.name,
                    }
                    current_task_obj.append(vals)
                return current_task_obj
            else:
                current_task = task_obj.search([('project_id', '=', name), ('stage_id', 'in', stages_selected)])
                for i in current_task:
                    vals = {
                        'name': i.name,
                        'user_id': i.user_id.name,
                        'stage_id': i.stage_id.name,
                    }
                    current_task_obj.append(vals)
                return current_task_obj
        else:
            if len(wizard_record.stage_select) == 0:
                current_task = task_obj.search([('project_id', '=', name), ('user_id', 'in', users_selected)])
                for i in current_task:
                    vals = {
                        'name': i.name,
                        'user_id': i.user_id.name,
                        'stage_id': i.stage_id.name,
                    }
                    current_task_obj.append(vals)
                return current_task_obj
            else:
                current_task = task_obj.search(
                    [('project_id', '=', name), ('user_id', 'in', users_selected), ('stage_id', 'in', stages_selected)])
                for i in current_task:
                    vals = {
                        'name': i.name,
                        'user_id':  i.user_id.name,
                        'stage_id': i.stage_id.name,
                    }
                    current_task_obj.append(vals)
                return current_task_obj

    def get_issue_model(self, name):
        wizard_record = request.env['wizard.project.report'].search([])[-1]
        issue_obj = request.env['project.issue']
        task_obj = issue_obj
        users_selected = []
        stages_selected = []
        current_task_obj = []
        for elements in wizard_record.partner_select:
            users_selected.append(elements.id)
        for elements in wizard_record.stage_select:
            stages_selected.append(elements.id)
        if len(wizard_record.partner_select) == 0:
            if len(wizard_record.stage_select) == 0:
                current_task = task_obj.search([('project_id', '=', name)])
                for i in current_task:
                    vals = {
                        'name': i.name,
                        'user_id': i.user_id.name,
                        'stage_id': i.stage_id.name,
                    }
                    current_task_obj.append(vals)
                return current_task_obj
            else:
                current_task = task_obj.search([('project_id', '=', name), ('stage_id', 'in', stages_selected)])
                for i in current_task:
                    vals = {
                        'name': i.name,
                        'user_id': i.user_id.name,
                        'stage_id': i.stage_id.name,
                    }
                    current_task_obj.append(vals)
                return current_task_obj
        else:
            if len(wizard_record.stage_select) == 0:
                current_task = task_obj.search([('project_id', '=', name), ('user_id', 'in', users_selected)])
                for i in current_task:
                    vals = {
                        'name': i.name,
                        'user_id': i.user_id.name,
                        'stage_id': i.stage_id.name,
                    }
                    current_task_obj.append(vals)
                return current_task_obj
            else:
                current_task = task_obj.search(
                    [('project_id', '=', name), ('user_id', 'in', users_selected), ('stage_id', 'in', stages_selected)])
                for i in current_task:
                    vals = {
                        'name': i.name,
                        'user_id': i.user_id.name,
                        'stage_id': i.stage_id.name,
                    }
                    current_task_obj.append(vals)
                return current_task_obj

    def get_list_model_task(self, name):
        wizard_record = request.env['wizard.project.report'].search([])[-1]
        if wizard_record.task_select:
            return 2
        else:
            return 3

    def get_list_model_issue(self, name):
        wizard_record = request.env['wizard.project.report'].search([])[-1]
        if wizard_record.issue_select:
            return 2
        else:
            return 3

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        model = self.env['project.project'].search([('id', '=', docids)])
        get_task_model = self.get_task_model(docids),
        get_issue_model = self.get_issue_model(docids),
        get_list_model_task = self.get_list_model_task(docids),
        get_list_model_issue = self.get_list_model_issue(docids),
        docargs = {
            'doc': model,
            'get_task_model': get_task_model,
            'get_issue_model': get_issue_model,
            'get_list_model_task': get_list_model_task[0],
            'get_list_model_issue': get_list_model_issue[0],
        }

        return self.env['report'].render('project_report_pdf.project_report_template', docargs)

