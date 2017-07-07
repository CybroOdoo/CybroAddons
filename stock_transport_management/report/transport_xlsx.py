# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
import datetime


class TransportReportXls(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, obj):
        logged_users = self.env['res.company']._company_default_get('sale.order')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 16, 'align': 'vcenter', 'bg_color': '#D3D3D3', 'bold': True})
        format1.set_font_color('#000080')
        format2 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format({'font_size': 10, 'bold': True})
        format4 = workbook.add_format({'font_size': 10})
        format1.set_align('center')
        format2.set_align('center')
        format3.set_align('center')
        sheet.merge_range('A3:L3', "Transportation Report", format1)
        report_date = datetime.datetime.now().strftime("%m/%d/%Y")
        sheet.merge_range('K1:L1', report_date, format4)
        sheet.merge_range('A1:B1', logged_users.name, format4)
        if data['form']['start_date']:
            date_start = data['form']['start_date']
        else:
            date_start = ""
        if data['form']['end_date']:
            date_end = data['form']['end_date']
        else:
            date_end = ""
        if date_start:
            sheet.write('A5', "Date From :", format3)
            sheet.write('A6', date_start, format4)
        if date_end:
            sheet.write('C5', "Date To :", format3)
            sheet.write('C6', date_end, format4)
        sheet.merge_range('A8:B8', "Vehicle Name ", format2)
        sheet.merge_range('C8:D8', "Date", format2)
        sheet.merge_range('E8:F8', "Sale Order", format2)
        sheet.merge_range('G8:H8', "Delivery Order", format2)
        sheet.merge_range('I8:J8', "No of Parcels", format2)
        sheet.merge_range('K8', "Status", format2)
        if date_start and date_end:
            report_obj = self.env['vehicle.status'].search([('transport_date', ">=", date_start) and
                                                            ('transport_date', "<=", date_end)])
        else:
            report_obj = self.env['vehicle.status'].search([])
        row_number = 9
        col_number = 0
        for values in report_obj:
            sheet.merge_range(row_number, col_number, row_number, col_number + 1, values['name'], format3)
            sheet.merge_range(row_number, col_number + 2, row_number, col_number + 3, values['transport_date'], format3)
            sheet.merge_range(row_number, col_number + 4, row_number, col_number + 5,  values['sale_order'], format3)
            sheet.merge_range(row_number, col_number + 6, row_number, col_number + 7, values['delivery_order'], format3)
            sheet.merge_range(row_number, col_number + 8, row_number, col_number + 9, values['no_parcels'], format3)
            sheet.write(row_number, col_number + 10, values['state'], format3)
            row_number += 1

TransportReportXls('report.stock_transport_management.transport_report_xls.xlsx', 'vehicle.status')