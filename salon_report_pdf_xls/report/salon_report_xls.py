# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2015-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Avinash Nk(<http://www.cybrosys.com>)
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


class SalonReportXls(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, lines):
        company_details = lines.env['res.company'].browse(1)
        chairs_selected = data['form']['chair_select']
        user_selected = data['form']['user_select']
        stage_selected = data['form']['stage_select']
        if len(stage_selected) == 0:
            if len(user_selected) == 0:
                if len(chairs_selected) == 0:
                    salon_orders = lines.env['salon.order'].search([])
                else:
                    salon_orders = lines.env['salon.order'].search([('chair_id', 'in', chairs_selected)])
            else:
                if len(chairs_selected) == 0:
                    salon_orders = lines.env['salon.order'].search([('chair_user', 'in', user_selected)])
                else:
                    salon_orders = lines.env['salon.order'].search([('chair_id', 'in', chairs_selected),
                                                                    ('chair_user', 'in', user_selected)])
        else:
            if len(user_selected) == 0:
                if len(chairs_selected) == 0:
                    salon_orders = lines.env['salon.order'].search([('stage_id', 'in', stage_selected)])
                else:
                    salon_orders = lines.env['salon.order'].search([('chair_id', 'in', chairs_selected),
                                                                    ('stage_id', 'in', stage_selected)])
            else:
                if len(chairs_selected) == 0:
                    salon_orders = lines.env['salon.order'].search([('chair_user', 'in', user_selected),
                                                                    ('stage_id', 'in', stage_selected)])
                else:
                    salon_orders = lines.env['salon.order'].search([('chair_id', 'in', chairs_selected),
                                                                    ('chair_user', 'in', user_selected),
                                                                    ('stage_id', 'in', stage_selected)])
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 22, 'bold': True, 'bg_color': '#D3D3D3'})
        format2 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format1.set_align('center')
        sheet.merge_range('A1:B1', company_details.name, format5)
        sheet.merge_range('A2:B2', company_details.street, format5)
        sheet.write('A3', company_details.city, format5)
        sheet.write('B3', company_details.zip, format5)
        sheet.merge_range('A4:B4', company_details.state_id.name, format5)
        sheet.merge_range('A5:B5', company_details.country_id.name, format5)
        sheet.merge_range('G1:H1', company_details.rml_header1, format5)
        sheet.merge_range(5, 0, 6, 7, "Salon Orders", format1)
        sheet.merge_range(7, 0, 7, 7, "", format3)
        sheet.merge_range(8, 0, 8, 1, "Order", format2)
        sheet.write(8, 2, "Chair", format2)
        sheet.merge_range(8, 3, 8, 4, "User", format2)
        sheet.write(8, 5, "Stage", format2)
        sheet.merge_range(8, 6, 8, 7, "Total", format2)
        row_number = 8
        sum = 0.0
        for records in salon_orders:
            sum += records.price_subtotal
            row_number += 1
            sheet.merge_range(row_number, 0, row_number, 1, records.name, format3)
            sheet.write(row_number, 2, records.chair_id.name, format3)
            sheet.merge_range(row_number, 3, row_number, 4, records.chair_user.name, format3)
            sheet.write(row_number, 5, records.stage_id.name, format3)
            sheet.merge_range(row_number, 6, row_number, 7, records.price_subtotal, format3)
        sheet.merge_range(row_number+1, 0, row_number+1, 7, "", format3)
        sheet.merge_range(row_number+2, 0, row_number+3, 3, "", format3)
        sheet.merge_range(row_number+2, 4, row_number+3, 5, "Total", format2)
        sheet.merge_range(row_number+2, 6, row_number+3, 7, sum, format2)
        sheet.merge_range(0, 2, 4, 5, "", format5)
        sheet.merge_range(1, 6, 4, 7, "", format5)
SalonReportXls('report.salon_report_pdf_xls.salon_report_xls.xlsx', 'salon.order')

