"""One2many excel report"""
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
from odoo import models, fields

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class SelectReportExcel(models.Model):
    """Used to get the excel report function"""
    _name = 'report.excel'

    def get_xlsx_report(self, data, names, response):
        """Used to print the excel report"""
        sl = 0
        row_num = 7
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format(
            {'font_size': '12px', 'align': 'center'})
        date_style = workbook.add_format(
            {'text_wrap': True, 'bold': True, 'num_format': 'dd-mm-yyyy'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        sheet.merge_range('B2:I3', 'EXCEL REPORT', head)
        sheet.merge_range('A6:B6', 'Date:', date_style)
        sheet.merge_range('C6:D6', fields.Datetime.today(), date_style)
        for doc in names:
            sl += 1
            row_num += 1
            col_num = 0
            sheet.merge_range(row_num, col_num + 2, row_num,
                              col_num + 4, doc, cell_format)
            col_num += 1
        data_list = []
        for rec in data:
            for x in rec:
                if type(rec[x]) == tuple:
                    st = ''.join(map(str, rec[x]))
                    data_list.append({'data': st})
                else:
                    data_list.append({'data': rec[x]})
        sl = 3
        row_num = 7
        col_num = 4
        num = row_num + len(names) + 1
        for doc in data_list:
            sl += 1
            sheet.merge_range(row_num, col_num + 2, row_num,
                              col_num + 4, doc['data'], txt)
            row_num += 1
            if row_num == num:
                col_num += 3
                row_num = 7
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
