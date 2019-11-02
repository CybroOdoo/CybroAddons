# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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

    def _get_report_values(self, docids, data=None):
        name = data['record']
        wizard_record = request.env['wizard.project.report'].search([])[-1]
        task_obj = request.env['project.task']
        users_selected = []
        stages_selected = []
        for elements in wizard_record.partner_select:
            users_selected.append(elements.id)
        for elements in wizard_record.stage_select:
            stages_selected.append(elements.id)
        if wizard_record.partner_select:
            if wizard_record.stage_select:
                current_task = task_obj.search([('project_id', '=', name),
                                                ('user_id', 'in', users_selected),
                                                ('stage_id', 'in', stages_selected)])

            else:
                current_task = task_obj.search([('project_id', '=', name),
                                                ('user_id', 'in', users_selected)])

        else:
            if wizard_record.stage_select:
                current_task = task_obj.search([('project_id', '=', name),
                                                ('stage_id', 'in', stages_selected)])
            else:
                current_task = task_obj.search([('project_id', '=', name)])
        vals = []
        for i in current_task:
            vals.append({
                'name': i.name,
                'user_id': i.user_id.name,
                'stage_id': i.stage_id.name,
            })
        if current_task:
            return {
                'vals': vals,
                'name': current_task[0].project_id.name,
                'manager': current_task[0].project_id.user_id.name,
                'date_start': current_task[0].project_id.date_start,
                'date_end': current_task[0].project_id.date,
            }
        else:
            return {
                'vals': vals,
                'name': current_task.project_id.name,
                'manager': current_task.project_id.user_id.name,
                'date_start': current_task.project_id.date_start,
                'date_end': current_task.project_id.date,
            }




