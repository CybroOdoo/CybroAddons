"""Excel report"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import io
from odoo import fields, http
from odoo.http import content_disposition, request

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ExcelHttp(http.Controller):
    """Used to print the excel report"""
    @http.route('/get/excel', type='json', auth='user', methods=['POST'],
                csrf=False)
    def get_excel_report(self):
        """"Formats the excel report"""
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Report' + '.xlsx'))
            ]
        )
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        workbook.add_worksheet("Excel Report")
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        # Formats
        format1 = workbook.add_format(
            {'font_size': 15, 'align': 'center', 'bold': True})
        format1.set_font_color('#000080')
        format2 = workbook.add_format(
            {'font_size': 11, 'bold': True, 'border': 1, 'bg_color': '#928E8E'})
        format4 = workbook.add_format(
            {'font_size': 10, 'num_format': 'yyyy-m-d', 'bold': True})
        format2.set_align('center')
        format4.set_align('right')
        sheet.merge_range(1, 1, 1, 1,
                          'A', format1)
        sheet.write(2, 0, "Date :", format4)
        sheet.write(2, 1, fields.Datetime.today(), format4)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response
