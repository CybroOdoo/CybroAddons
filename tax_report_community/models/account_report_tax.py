# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Muhammed Dilshad Tk (odoo@cybrosys.com)
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
import io
import json
from odoo import api, models, _
from odoo.tools import date_utils
from datetime import datetime
from odoo.exceptions import UserError
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class AccountKitTaxReport(models.TransientModel):
    """ Inherits Account Kit Tax Report"""
    _inherit = 'kit.account.tax.report'

    def print_xls(self):
        """Prints excel report"""
        # fetches start and end date from wizard
        form = {'date_from': self.date_from,
                'date_to': self.date_to, }
        data = {
            'data': form,
            'lines': self.get_lines(form),
            'with_context': form
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'kit.account.tax.report',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Tax report',
                     },
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, data, response):
        """writing xlsx report values to excel sheet"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        if not data['data']:
            raise UserError(
                _("Form content is missing, this report cannot be printed."))
        sheet = workbook.add_worksheet('TAX REPORT')
        format1 = workbook.add_format(
            {'align': 'center', 'bg_color': '#D3D3D3', 'bold': True})
        sheet.merge_range('A1:C1', 'TAX REPORT', format1)
        sheet.write('A3', 'From', )
        sheet.set_column(0, 0, 50)
        sheet.set_column(1, 1, 10)
        sheet.set_column(2, 2, 10)
        sheet.write('B3', 'To', )
        sheet.write('A4', data['data']['date_from'], )
        sheet.write('B4', data['data']['date_to'], )
        i = 6
        sheet.write('A' + str(i), 'Sale', format1)
        sheet.write('B' + str(i), 'Net', format1)
        sheet.write('C' + str(i), 'Tax', format1)
        i += 1
        for line in data['lines']['sale']:
            sheet.write('A' + str(i), line.get('name'), )
            sheet.write('B' + str(i), line.get('net'), )
            sheet.write('C' + str(i), line.get('tax'), )
            i += 1
        sheet.write('A' + str(i), 'Purchase', format1)
        sheet.write('B' + str(i), 'Net', format1)
        sheet.write('C' + str(i), 'Tax', format1)
        i += 1
        for line in data['lines']['purchase']:
            sheet.write('A' + str(i), line.get('name'), )
            sheet.write('B' + str(i), line.get('net'), )
            sheet.write('C' + str(i), line.get('tax'), )
            i += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def _get_report_values(self, docids, data=None):
        """ Gets the report values """
        if not data.get('form'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))
        return {
            'data': data['form'],
            'lines': self.get_lines(data.get('form')),
        }

    def _sql_from_amls_one(self):
        """Taking data from account_move_line one using sql query"""
        sql = """SELECT "account_move_line".tax_line_id, COALESCE(SUM
        ("account_move_line".debit-"account_move_line".credit), 0)
                        FROM %s
                        WHERE %s  GROUP BY "account_move_line".tax_line_id"""
        return sql

    def _sql_from_amls_two(self):
        """Taking data from account_move_line two using sql query"""
        sql = """SELECT r.account_tax_id, COALESCE(SUM("account_move_line".
        debit-"account_move_line".credit), 0)
                     FROM %s
                     INNER JOIN account_move_line_account_tax_rel r ON 
                     ("account_move_line".id = r.account_move_line_id)
                     INNER JOIN account_tax t ON (r.account_tax_id = t.id)
                     WHERE %s  GROUP BY r.account_tax_id"""
        return sql

    def _compute_from_amls(self, options, taxes):
        """Compute data from account_move_line's"""
        # compute the tax amount
        sql = self._sql_from_amls_one()
        tables, where_clause, where_params = self.env[
            'account.move.line']._query_get()
        query = sql % (tables, where_clause)
        self.env.cr.execute(query, where_params)
        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in taxes:
                taxes[result[0]]['tax'] = abs(result[1])
        # compute the net amount
        sql2 = self._sql_from_amls_two()
        query = sql2 % (tables, where_clause)
        self.env.cr.execute(query, where_params)
        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in taxes:
                taxes[result[0]]['net'] = abs(result[1])

    @api.model
    def get_lines(self, options):
        """Get taxes datas"""
        taxes = {}
        for tax in self.env['account.tax'].search(
                [('type_tax_use', '!=', 'none')]):
            if tax.children_tax_ids:
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        continue
                    taxes[child.id] = {'tax': 0, 'net': 0, 'name': child.name,
                                       'type': tax.type_tax_use}
            else:
                taxes[tax.id] = {'tax': 0, 'net': 0, 'name': tax.name,
                                 'type': tax.type_tax_use}
        if options['date_from']:
            self.with_context(date_from=options['date_from'],
                              strict_range=True)._compute_from_amls(options,
                                                                    taxes)
        elif options['date_to']:
            self.with_context(date_to=options['date_to'],
                              strict_range=True)._compute_from_amls(options,
                                                                    taxes)
        elif options['date_from'] and options['date_to']:
            self.with_context(date_from=options['date_from'],
                              date_to=options['date_to'],
                              strict_range=True)._compute_from_amls(options,
                                                                    taxes)
        else:
            date_to = str(datetime.today().date())
            self.with_context(date_to=date_to,
                              strict_range=True)._compute_from_amls(options,
                                                                    taxes)
        groups = dict((tp, []) for tp in ['sale', 'purchase'])
        for tax in taxes.values():
            if tax['tax']:
                groups[tax['type']].append(tax)
        return groups
