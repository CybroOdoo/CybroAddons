# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Avinash Nk(<avinash@cybrosys.in>)
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
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class EventReportXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, obj):
        parser_obj = self.env['report.event_management_report.event_report_template']
        filtered_records = parser_obj.filtered_records(data)
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 16, 'align': 'center', 'bg_color': '#D3D3D3', 'bold': True})
        format1.set_font_color('#000080')
        format2 = workbook.add_format({'font_size': 10, 'bold': True})
        format3 = workbook.add_format({'font_size': 10})
        format1.set_align('center')
        format2.set_align('center')
        sheet.merge_range('A01:B01', "Name", format2)
        sheet.merge_range('C01:D01', "Type", format2)
        sheet.merge_range('E01:F01', "Customer", format2)
        sheet.merge_range('G01:H01', "Date", format2)
        sheet.merge_range('I01:J01', "Start Date", format2)
        sheet.merge_range('K01:L01', "End Date", format2)
        sheet.merge_range('M01:N01', "State", format2)
        row_number = 1
        col_number = 0
        for records in filtered_records:
            sheet.merge_range(row_number, col_number, row_number, col_number+1, records.name, format3)
            sheet.merge_range(row_number, col_number+2, row_number, col_number+3, records.type_of_event.name, format3)
            sheet.merge_range(row_number, col_number+4, row_number, col_number+5, records.partner_id.name, format3)
            sheet.merge_range(row_number, col_number+6, row_number, col_number+7, records.date, format3)
            sheet.merge_range(row_number, col_number+8, row_number, col_number+9, records.start_date, format3)
            sheet.merge_range(row_number, col_number+10, row_number, col_number+11, records.end_date, format3)
            sheet.merge_range(row_number, col_number+12, row_number, col_number+13, records.state, format3)
            row_number += 1


EventReportXlsx('report.event_management_report.event_report.xlsx', 'event.management')
