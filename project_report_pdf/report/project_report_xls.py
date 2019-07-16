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
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx


class ProjectReportXls(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 22, 'bg_color': '#D3D3D3'})
        format4 = workbook.add_format({'font_size': 22})
        format2 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format6 = workbook.add_format({'font_size': 22, 'bg_color': '#FFFFFF'})
        format7.set_align('center')
        if lines.company_id.state_id.name == False:
            state_name = ""
        else:
            state_name = lines.company_id.state_id.name
        if lines.company_id.country_id.name == False:
            country_name = ""
        else:
            country_name = lines.company_id.country_id.name
        sheet.merge_range('A1:B1', lines.company_id.name, format5)
        sheet.merge_range('A2:B2', lines.company_id.street, format5)
        sheet.write('A3', lines.company_id.city, format5)
        sheet.write('B3', lines.company_id.zip, format5)
        sheet.merge_range('A4:B4', state_name, format5)
        sheet.merge_range('A5:B5', country_name, format5)
        sheet.merge_range('G1:H1', lines.company_id.rml_header1, format5)
        sheet.merge_range(5, 0, 6, 1, "Project  :", format1)
        sheet.merge_range(5, 2, 6, 7, lines.name, format1)
        sheet.merge_range('A8:B8', "Project Manager    :", format5)
        sheet.merge_range('C8:D8', lines.user_id.name, format5)
        if lines.date_start:
            date_start = lines.date_start
        else:
            date_start = ""
        if lines.date:
            date_end = lines.date
        else:
            date_end = ""
        sheet.merge_range('A9:B9', "Start Date             :", format5)
        sheet.merge_range('C9:D9', date_start, format5)
        sheet.merge_range('A10:B10', "End Date               :", format5)
        sheet.merge_range('C10:D10', date_end, format5)
        row_number = 10

        sheet.merge_range(0, 2, 4, 5, "", format5)
        sheet.merge_range(1, 6, 4, 7, "", format5)
        sheet.merge_range(7, 4, 9, 7, "", format5)


        if data['form']['task_select'] == True :

            sheet.merge_range(10, 4, 11, 7, "", format5)
            sheet.merge_range(row_number, 0, row_number+1, 3, "Open Tasks", format4)
            row_number += 2
            task_obj = self.env['project.task']
            if len(data['form']['partner_select']) == 0:
                if len(data['form']['stage_select']) == 0:
                    current_task_obj = task_obj.search([('project_id', '=', lines.id)])
                else:
                    current_task_obj = task_obj.search(
                        [('project_id', '=', lines.id), ('stage_id', 'in', data['form']['stage_select'])])
            else:
                if len(data['form']['stage_select']) == 0:
                    current_task_obj = task_obj.search(
                        [('project_id', '=', lines.id), ('user_id', 'in', data['form']['partner_select'])])
                else:
                    current_task_obj = task_obj.search(
                        [('project_id', '=', lines.id), ('user_id', 'in', data['form']['partner_select']),
                         ('stage_id', 'in', data['form']['stage_select'])])

            sheet.merge_range(row_number, 0, row_number, 3, "Tasks", format2)
            sheet.merge_range(row_number, 4, row_number, 5, "Assigned", format2)
            sheet.merge_range(row_number, 6, row_number, 7, "Stage", format2)
            for records in current_task_obj:
                row_number += 1
                if records.user_id.name:
                    user_name = records.user_id.name
                else:
                    user_name = ""
                sheet.merge_range(row_number, 0, row_number, 3, records.name, format3)
                sheet.merge_range(row_number, 4, row_number, 5, user_name, format3)
                sheet.merge_range(row_number, 6, row_number, 7, records.stage_id.name, format3)
            row_number += 1
        if data['form']['issue_select'] == True :

            row_number += 1
            sheet.merge_range(row_number-1, 0, row_number-1, 7, "", format4)
            sheet.merge_range(row_number, 4, row_number + 1, 7, "", format5)
            sheet.merge_range(row_number, 0, row_number+1, 3, "Open Issues", format6)
            row_number += 2
            task_obj = self.env['project.issue']


            if len(data['form']['partner_select']) == 0:
                if len(data['form']['stage_select']) == 0:
                    current_task_obj = task_obj.search([('project_id', '=', lines.id)])
                else:
                    current_task_obj = task_obj.search(
                        [('project_id', '=', lines.id), ('stage_id', 'in', data['form']['stage_select'])])
            else:
                if len(data['form']['stage_select']) == 0:
                    current_task_obj = task_obj.search(
                        [('project_id', '=', lines.id), ('user_id', 'in', data['form']['partner_select'])])
                else:
                    current_task_obj = task_obj.search(
                        [('project_id', '=', lines.id), ('user_id', 'in', data['form']['partner_select']),
                         ('stage_id', 'in', data['form']['stage_select'])])

            sheet.merge_range(row_number, 0, row_number, 3, "Issues", format2)
            sheet.merge_range(row_number, 4, row_number, 5, "Assigned", format2)
            sheet.merge_range(row_number, 6, row_number, 7, "Stage", format2)
            for records in current_task_obj:
                row_number += 1
                if records.user_id.name:
                    user_name = records.user_id.name
                else:
                    user_name = ""
                sheet.merge_range(row_number, 0, row_number, 3, records.name, format3)
                sheet.merge_range(row_number, 4, row_number, 5, user_name, format3)
                sheet.merge_range(row_number, 6, row_number, 7, records.stage_id.name, format3)
        row_number += 2
        sheet.merge_range(row_number, 0, row_number, 1, lines.company_id.phone, format7)
        sheet.merge_range(row_number, 2, row_number, 4, lines.company_id.email, format7)
        sheet.merge_range(row_number, 5, row_number, 7, lines.company_id.website, format7)

ProjectReportXls('report.project_report_pdf.project_report_xls.xlsx', 'project.project')