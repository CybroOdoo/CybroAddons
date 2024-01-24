# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, models


class ReportProjectPdfProjectReportTemplate(models.AbstractModel):
    """ Pdf reports """
    _name = 'report.project_report_pdf.report_project_project'
    _description = 'Project Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """ The method collects task data based on selected criteria, including
        assigned partners and task stages for the pdf report. """
        name = data['record']
        wizard_record = self.env['project.report'].search([])[-1]
        task_obj = self.env['project.task']
        users_selected = []
        stages_selected = []
        for elements in wizard_record.partner_select:
            users_selected.append(elements.id)
        for elements in wizard_record.stage_select:
            stages_selected.append(elements.id)
        if wizard_record.partner_select:
            if wizard_record.stage_select:
                current_task = task_obj.search([
                    ('project_id', '=', name),
                    ('user_ids', 'in', users_selected),
                    ('stage_id', 'in', stages_selected)])
            else:
                current_task = task_obj.search([('project_id', '=', name),
                                                ('user_ids', 'in',
                                                 users_selected)])
        else:
            if wizard_record.stage_select:
                current_task = task_obj.search([('project_id', '=', name),
                                                ('stage_id', 'in',
                                                 stages_selected)])
            else:
                current_task = task_obj.search([('project_id', '=', name)])
        vals = []
        for i in current_task:
            new = []
            new.clear()
            for o in i.user_ids:
                new.append(o.name)
            assignees_name = ' , '.join([str(elem) for elem in new])
            vals.append({
                'name': i.name,
                'user_id': assignees_name,
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
