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
import io
import json

import xlsxwriter

from odoo import api, fields, models
from odoo.tools.json import json_default


class ProjectReport(models.TransientModel):
    """ This model represents a wizard for generating project reports in both
    PDF and XLS formats."""
    _name = 'project.report'
    _description = 'Project Report'

    project_id = fields.Many2one(
        'project.project',
        default=lambda self: self.env.context.get('active_id'),
        help="Project whose tasks are printed.")
    user_ids = fields.Many2many(
        'res.users',
        string='Assigned to',
        help="Only tasks assigned to these users are included.")
    stage_ids = fields.Many2many(
        'project.task.type',
        help="Only tasks in these stages are included.")

    @api.model
    def _get_task_lines(self, project_id, user_ids=None, stage_ids=None):
        """ Return the task rows (name, assignees, stage) of a project,
        optionally filtered by assignee and stage. """
        if not project_id:
            return []
        domain = [('project_id', '=', project_id)]
        if user_ids:
            domain.append(('user_ids', 'in', user_ids))
        if stage_ids:
            domain.append(('stage_id', 'in', stage_ids))
        return [{
            'name': task.name,
            'user_id': ', '.join(task.user_ids.mapped('name')),
            'stage_id': task.stage_id.name or '',
        } for task in self.env['project.task'].search(domain)]

    def _get_report_data(self):
        """ Return the options shared by the PDF and XLS reports. """
        self.ensure_one()
        return {
            'project_id': self.project_id.id,
            'user_ids': self.user_ids.ids,
            'stage_ids': self.stage_ids.ids,
        }

    def print_project_report_pdf(self):
        """ Open the PDF report for the selected filters. """
        report_action = self.env.ref(
            'project_report_pdf.action_report_project_project',
        ).report_action(self, data=self._get_report_data())
        report_action.update({'close_on_report_download': True})
        return report_action

    def print_project_report_xls(self):
        """ Download the XLSX report for the selected filters. """
        return {
            'type': 'ir.actions.report',
            'data': {
                'options': json.dumps(
                    self._get_report_data(), default=json_default),
                'output_format': 'xlsx',
            },
            'report_type': 'xlsx',
        }

    @api.model
    def get_xlsx_report(self, data, response):
        """ This function uses the XlsxWriter library for generating XLSX
        reports. The report includes company information, project details,
        and task data.
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        project = self.env['project.project'].browse(
            data.get('project_id') or [])
        company = self.env.company
        vals = self._get_task_lines(
            project.id, data.get('user_ids'), data.get('stage_ids'))

        sheet = workbook.add_worksheet(self.env._("Project Report"))
        format1 = workbook.add_format({'font_size': 22, 'bg_color': '#D3D3D3'})
        format4 = workbook.add_format({'font_size': 22})
        format2 = workbook.add_format(
            {'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7.set_align('center')
        sheet.merge_range('A1:B1', company.name or '', format5)
        sheet.merge_range('A2:B2', company.street or '', format5)
        sheet.write('A3', company.city or '', format5)
        sheet.write('B3', company.zip or '', format5)
        sheet.merge_range('A4:B4', company.state_id.name or '', format5)
        sheet.merge_range('A5:B5', company.country_id.name or '', format5)
        sheet.merge_range(5, 0, 6, 1, self.env._("Project:"), format1)
        sheet.merge_range(5, 2, 6, 7, project.name or '', format1)
        sheet.merge_range(
            'A8:B8', self.env._("Project Manager:"), format5)
        sheet.merge_range('C8:D8', project.user_id.name or '', format5)
        sheet.merge_range(
            'A9:B9', self.env._("Start Date:"), format5)
        sheet.merge_range(
            'C9:D9', str(project.date_start or ''), format5)
        sheet.merge_range(
            'A10:B10', self.env._("End Date:"), format5)
        sheet.merge_range('C10:D10', str(project.date or ''), format5)
        sheet.merge_range(0, 2, 4, 5, "", format5)
        sheet.merge_range(1, 6, 4, 7, "", format5)
        sheet.merge_range(7, 4, 9, 7, "", format5)
        sheet.merge_range(10, 4, 11, 7, "", format5)
        sheet.merge_range('A11:D12', self.env._("Tasks"), format4)
        sheet.merge_range('A13:D13', self.env._("Task"), format2)
        sheet.merge_range('E13:G13', self.env._("Assigned"), format2)
        sheet.merge_range('H13:I13', self.env._("Stage"), format2)
        row_number = 13
        for val in vals:
            sheet.merge_range(
                row_number, 0, row_number, 3, val['name'] or '', format3)
            sheet.merge_range(
                row_number, 4, row_number, 6, val['user_id'], format3)
            sheet.merge_range(
                row_number, 7, row_number, 8, val['stage_id'], format3)
            row_number += 1
        row_number += 1
        sheet.merge_range(
            row_number, 0, row_number, 1, company.phone or '', format7)
        sheet.merge_range(
            row_number, 2, row_number, 4, company.email or '', format7)
        sheet.merge_range(
            row_number, 5, row_number, 7, company.website or '', format7)
        workbook.close()
        response.stream.write(output.getvalue())
        output.close()
