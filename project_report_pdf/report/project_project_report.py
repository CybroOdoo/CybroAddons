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
from odoo import api, models


class ReportProjectPdfProjectReportTemplate(models.AbstractModel):
    """ Values of the project task PDF report. """
    _name = 'report.project_report_pdf.report_project_project'
    _description = 'Project Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """ Collect the project and its tasks, filtered by the assignees and
        stages selected in the wizard, for the PDF report. """
        data = data or {}
        wizard = self.env['project.report'].browse(docids).exists()[:1]
        project = self.env['project.project'].browse(
            data.get('project_id') or wizard.project_id.id)
        user_ids = data.get('user_ids', wizard.user_ids.ids)
        stage_ids = data.get('stage_ids', wizard.stage_ids.ids)
        return {
            'doc_ids': docids,
            'doc_model': 'project.project',
            'docs': project,
            'vals': self.env['project.report']._get_task_lines(
                project.id, user_ids, stage_ids),
            'name': project.name or '',
            'manager': project.user_id.name or '',
            'date_start': project.date_start or '',
            'date_end': project.date or '',
        }
