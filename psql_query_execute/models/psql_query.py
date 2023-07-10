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
import json
import io
from odoo import fields, models, _
from odoo.tools import date_utils
from odoo.exceptions import ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class PsqlQuery(models.Model):
    """ This model executes a query directly in the Odoo user interface. """
    _name = 'psql.query'
    _description = 'PostgreSQL Query'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, help="Query Name")
    query_name = fields.Text(string='Query', required=True, help="Type the query to execute")
    query_result = fields.Html(string='Result', readonly=True, help="Data output of the query")

    def action_execute_query(self):
        """Execute the query operation"""
        try:
            if self.query_name:
                self._cr.execute(self.query_name)
                keys = [i[0] for i in self._cr.description]
                table_header = ''
                table_datas = ''
                for key in keys:
                    table_header += "<th style='border:1px solid black !important'>%s</th>" % key
                query_result = self._cr.fetchall()
                for query_res in query_result:
                    table_datas += "<tr>"
                    for res in query_res:
                        table_datas += "<td style='border:1px solid black !important'>{0}</td>".format(res)
                    table_datas += "</tr>"
                self.query_result = """<div style="overflow:auto;"><table class="table text-center table-border table-sm"
                             style="width:max-content";><thead>
                            <tr style='border:1px solid black !important;background: lightblue;'>
                            """ + str(table_header) + """</tr></thead><tbody>""" + str(
                    table_datas) + """</tbody></table></div>"""
        except Exception as error:
            raise ValidationError(_('Error executing SQL query: %s ', error))

    def _get_report_data(self):
        """Get the value of the data for which the query was executed"""
        today = fields.Datetime.now().date()
        result = []
        keys = ''
        try:
            if self.query_name:
                self._cr.execute(self.query_name)
                keys = [i[0] for i in self._cr.description]
            for data in self._cr.fetchall():
                result.append(data)
        except Exception as error:
            raise ValidationError(_('Error executing SQL query: %s ', error))
        datas = {
            'ids': self,
            'model': 'psql.query',
            'no_value': False,
            'header': keys,
            'form': result,
            'date': today,
        }
        return datas

    def action_print_query_result_xlsx(self):
        """Print the query result in Xlsx report"""
        datas = self._get_report_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'psql.query',
                     'output_format': 'xlsx',
                     'options': json.dumps(datas, default=date_utils.json_default),
                     'report_name': 'Query Report',
                     },
        }

    def get_xlsx_report(self, data, response):
        """Set the position to print the data in xlsx file"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_default_row(19)
        cmp_name = self.env.user.company_id.name or ''
        txt_1 = workbook.add_format(
            {'font_size': '10px', 'bold': True, 'align': 'center',
             'color': '#423642'})
        date_now = data['date']
        sheet.merge_range('A1:B1', 'Report Date: ' + date_now, txt_1)
        sheet.merge_range('A2:B2', cmp_name, txt_1)
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#edd8ed', 'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'bg_color': '#edd8ed', 'border': 1})
        count = 0
        row_number = 4
        record = data['header']
        column_number = 0
        for row in record:
            count += 1
            sheet.merge_range(row_number - 1, column_number, row_number, column_number,
                              row, format3)
            column_number += 1
        row_number = 5
        for val in data['form']:
            column_number = 0
            for values in val:
                if values is None:
                    sheet.write(row_number, column_number, 'None', format1)
                else:
                    sheet.write(row_number, column_number, values, format1)
                sheet.set_column(row_number, column_number, 15)
                column_number += 1
            row_number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
