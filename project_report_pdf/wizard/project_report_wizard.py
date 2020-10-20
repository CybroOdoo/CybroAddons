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
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import json
import datetime
import pytz
import io
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ProjectReportButton(models.TransientModel):
    _name = 'wizard.project.report'

    partner_select = fields.Many2many('res.users', string='Assigned to')
    stage_select = fields.Many2many('project.task.type', string="Stage")

    def print_project_report_pdf(self):

        active_record = self._context['active_id']
        record = self.env['project.project'].browse(active_record)

        data = {
            'ids': self.ids,
            'model': self._name,
            'record': record.id,
            'partner_select': self.partner_select
        }
        return self.env.ref('project_report_pdf.report_project_pdf').report_action(self, data=data)

    def print_project_report_xls(self):
        active_record = self._context['active_id']
        record = self.env['project.project'].browse(active_record)
        data = {
            'ids': self.ids,
            'model': self._name,
            'record': record.id,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'wizard.project.report',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Project Report',
                     },
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        name = data['record']
        user_obj = self.env.user
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
                'user_id': i.user_id.name if i.user_id.name else '',
                'stage_id': i.stage_id.name,
            })
        if current_task:
            project_name = current_task[0].project_id.name
            user = current_task[0].project_id.user_id.name
        else:
            project_name = current_task.project_id.name
            user = current_task.project_id.user_id.name
        sheet = workbook.add_worksheet("Project Report")
        format1 = workbook.add_format({'font_size': 22, 'bg_color': '#D3D3D3'})
        format4 = workbook.add_format({'font_size': 22})
        format2 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7.set_align('center')
        sheet.merge_range('A1:B1', user_obj.company_id.name, format5)
        sheet.merge_range('A2:B2', user_obj.company_id.street, format5)
        sheet.write('A3', user_obj.company_id.city, format5)
        sheet.write('B3', user_obj.company_id.zip, format5)
        sheet.merge_range('A4:B4', user_obj.company_id.state_id.name, format5)
        sheet.merge_range('A5:B5', user_obj.company_id.country_id.name, format5)
        sheet.merge_range('C1:H5', "", format5)
        sheet.merge_range(5, 0, 6, 1, "Project  :", format1)
        if project_name:
            sheet.merge_range(5, 2, 6, 7, project_name, format1)
        sheet.merge_range('A8:B8', "Project Manager    :", format5)
        if user:
            sheet.merge_range('C8:D8', user, format5)
        date_start = ''
        date_end = ''
        if current_task:
            date_start = str(current_task[0].project_id.date_start)
        if current_task:
            date_end = str(current_task[0].project_id.date)
        sheet.merge_range('A9:B9', "Start Date              :", format5)
        if not date_start:
            sheet.merge_range('C9:D9', '', format5)
        else:
            sheet.merge_range('C9:D9', date_start, format5)
        sheet.merge_range('A10:B10', "End Date                :", format5)
        if str(date_end):
            sheet.merge_range('C10:D10', date_end, format5)
        sheet.merge_range(0, 2, 4, 5, "", format5)
        sheet.merge_range(1, 6, 4, 7, "", format5)
        sheet.merge_range(7, 4, 9, 7, "", format5)
        sheet.merge_range(10, 4, 11, 7, "", format5)
        sheet.merge_range('A11:H12', 'Open Tasks', format4)
        sheet.merge_range('A13:D13', "Tasks", format2)
        sheet.merge_range('E13:F13', "Assigned", format2)
        sheet.merge_range('G13:H13', "Stage", format2)
        row_number = 13
        column_number = 0
        for val in vals:
            sheet.merge_range(row_number, column_number, row_number, column_number + 3, val['name'], format3)
            sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['user_id'], format3)
            sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, val['stage_id'], format3)
            row_number += 1

        row_number += 1
        sheet.merge_range(row_number, 0, row_number, 1, user_obj.company_id.phone, format7)
        sheet.merge_range(row_number, 2, row_number, 4, user_obj.company_id.email, format7)
        sheet.merge_range(row_number, 5, row_number, 7, user_obj.company_id.website, format7)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

