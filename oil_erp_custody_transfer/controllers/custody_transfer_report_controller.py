# -*- coding: utf-8 -*-
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################
import io
import json
import xlsxwriter
from odoo import http
from odoo.http import request, content_disposition


class CustodyTransferReportController(http.Controller):

    @http.route('/oil_erp_custody_transfer/report_xlsx', type='http', auth='user')
    def report_xlsx(self, domain=None, **kwargs):
        domain_list = json.loads(domain) if domain else []
        records = request.env['custody.transfer'].search(domain_list)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Custody Transfer')

        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter',
        })
        header_fmt = workbook.add_format({
            'bold': True, 'font_size': 10,
            'font_color': '#000000', 'bg_color': '#F2F2F2',
            'border': 1, 'align': 'center', 'valign': 'vcenter',
        })
        cell_fmt = workbook.add_format({
            'font_size': 10, 'border': 1, 'align': 'left', 'valign': 'vcenter',
        })
        num_fmt = workbook.add_format({
            'font_size': 10, 'border': 1, 'align': 'right',
            'valign': 'vcenter', 'num_format': '#,##0.00',
        })
        total_fmt = workbook.add_format({
            'bold': True, 'font_size': 10, 'border': 1,
            'align': 'right', 'bg_color': '#F2F2F2', 'num_format': '#,##0.00',
        })

        company = request.env.company.name
        worksheet.merge_range(0, 0, 0, 11, company, title_fmt)
        worksheet.merge_range(1, 0, 1, 11, 'Custody Transfer Report', title_fmt)

        purpose_labels = {
            'commercial_sale': 'Commercial Sale', 'inter_facility': 'Inter-Facility',
            'emergency': 'Emergency', 'intercompany': 'Intercompany',
            'pipeline_injection': 'Pipeline Injection', 'other': 'Other',
        }

        headers = [
            'Transfer #', 'Date', 'Purpose', 'Operation Type',
            'Legal Owner', 'Custodian', 'Carrier',
            'Planned Qty', 'Actual Qty', 'Variance', 'Demurrage Cost', 'Status',
        ]
        col_widths = [18, 14, 20, 20, 22, 22, 22, 13, 13, 13, 15, 14]
        for col, (h, w) in enumerate(zip(headers, col_widths)):
            worksheet.write(3, col, h, header_fmt)
            worksheet.set_column(col, col, w)
        worksheet.set_row(3, 18)

        row = 4
        total_planned = total_actual = total_variance = total_demurrage = 0.0
        for rec in records:
            date_str = rec.transfer_date.strftime('%Y-%m-%d') if rec.transfer_date else ''
            worksheet.write(row, 0, rec.name or '', cell_fmt)
            worksheet.write(row, 1, date_str, cell_fmt)
            worksheet.write(row, 2, purpose_labels.get(rec.transfer_purpose or '', '-'), cell_fmt)
            worksheet.write(row, 3, rec.picking_type_id.name or '-', cell_fmt)
            worksheet.write(row, 4, rec.owner_partner_id.name or '-', cell_fmt)
            worksheet.write(row, 5, rec.custodian_partner_id.name or '-', cell_fmt)
            worksheet.write(row, 6, rec.carrier_partner_id.name or '-', cell_fmt)
            worksheet.write_number(row, 7, rec.total_planned_qty, num_fmt)
            worksheet.write_number(row, 8, rec.total_actual_qty, num_fmt)
            worksheet.write_number(row, 9, rec.total_variance_qty, num_fmt)
            worksheet.write_number(row, 10, rec.demurrage_cost, num_fmt)
            worksheet.write(row, 11, rec.state.replace('_', ' ').upper(), cell_fmt)
            total_planned += rec.total_planned_qty
            total_actual += rec.total_actual_qty
            total_variance += rec.total_variance_qty
            total_demurrage += rec.demurrage_cost
            row += 1

        total_label_fmt = workbook.add_format({
            'bold': True, 'font_size': 10, 'border': 1,
            'align': 'right', 'bg_color': '#F2F2F2',
        })
        worksheet.merge_range(row, 0, row, 6, 'TOTAL', total_label_fmt)
        worksheet.write_number(row, 7, total_planned, total_fmt)
        worksheet.write_number(row, 8, total_actual, total_fmt)
        worksheet.write_number(row, 9, total_variance, total_fmt)
        worksheet.write_number(row, 10, total_demurrage, total_fmt)
        worksheet.write(row, 11, '', workbook.add_format({'border': 1, 'bg_color': '#F2F2F2'}))

        worksheet.write(row + 2, 0, 'OIL ERP POWERED REPORTING',
                        workbook.add_format({'italic': True, 'font_color': '#888888'}))

        workbook.close()
        output.seek(0)
        filename = 'Custody_Transfer_Report.xlsx'
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename)),
            ],
        )
