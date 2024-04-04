# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (odoo@cybrosys.com)
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
################################################################################
import json
from datetime import datetime
from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools import date_utils, io

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class AccountWizard(models.TransientModel):
    _name = "account.wizard"
    _description = 'Account Wizard'

    name = fields.Char(default="Invoice", help='Name of Invoice ')
    date_from = fields.Date(string="Start Date", required=True,
                            help='Date at which report need to be start')
    date_to = fields.Date(string="End Date", default=fields.Date.today,
                          required=True,
                          help='Date at which report need to be end')
    today = fields.Date("Report Date", default=fields.Date.today,
                        help='Date at which report is generated')
    levels = fields.Selection([('summary', 'Summary'),
                               ('consolidated', 'Consolidated'),
                               ('detailed', 'Detailed'),
                               ('very', 'Very Detailed')],
                              string='Levels', required=True, default='summary',
                              help='Different levels for cash flow statements\n'
                                   'Summary: Month wise report.\n'
                                   'Consolidated: Based on account types.\n'
                                   'Detailed: Based on accounts.\n'
                                   'Very Detailed: Accounts with their move lines')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True,
                                   default='posted', help='Type of entries')

    def generate_pdf_report(self):
        """ Generate the pdf reports and return values to template"""
        self.ensure_one()
        logged_users = self.env['res.company']._company_default_get(
            'account.account')
        if self.date_from:
            if self.date_from > self.date_to:
                raise UserError(_("Start date should be less than end date"))
        data = {
            'ids': self.ids,
            'model': self._name,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'levels': self.levels,
            'target_move': self.target_move,
            'today': self.today,
            'logged_users': logged_users.name,
        }
        return self.env.ref(
            'advance_cash_flow_statements.pdf_report_action').report_action(
            self,
            data=data)

    def generate_xlsx_report(self):
        """ Generate xlsx report return values to template"""
        date_from = datetime.strptime(str(self.date_from), "%Y-%m-%d")
        date_to = datetime.strptime(str(self.date_to), "%Y-%m-%d")
        if date_from:
            if date_from > date_to:
                raise UserError(_("Start date should be less than end date"))
        data = {
            'ids': self.ids,
            'model': self._name,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'levels': self.levels,
            'target_move': self.target_move,
            'today': self.today,
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'account.wizard',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Adv Cash Flow Statement',
                     },
        }

    def get_xlsx_report(self, data, response):
        """ Update the xlsx template and pass values to templates"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        fetched_data = []
        account_res = []
        journal_res = []
        fetched = []
        currency_symbol = self.env.user.company_id.currency_id.symbol
        if data['levels'] == 'summary':
            state = """ WHERE am.state = 'posted' """ if data[
                                                             'target_move'] == 'posted' else ''
            query3 = """SELECT to_char(am.date, 'Month') as month_part, extract(
            YEAR from am.date) as year_part, sum(aml.debit) AS total_debit, sum(
            aml.credit) AS total_credit, sum(aml.balance) AS total_balance FROM(
            SELECT am.date, am.id, am.state FROM account_move as am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         WHERE am.date BETWEEN '""" + str(
                data['date_from']) + """' and '""" + str(
                data['date_to']) + """' ) am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         """ + state + """GROUP BY month_part,year_part"""
            cr = self._cr
            cr.execute(query3)
            fetched_data = cr.dictfetchall()
        elif data['levels'] == 'consolidated':
            state = """ WHERE am.state = 'posted' """ if data[
                                                             'target_move'] == 'posted' else ''
            query2 = """SELECT aa.id,aa.name, sum(aml.debit) AS total_debit, sum(
            aml.credit) AS total_credit,sum(aml.balance) AS total_balance FROM (
                         SELECT am.id, am.state FROM account_move as am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         WHERE am.date BETWEEN '""" + str(
                data['date_from']) + """' and '""" + str(
                data['date_to']) + """' ) am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         """ + state + """GROUP BY aa.id,aa.name"""
            cr = self._cr
            cr.execute(query2)
            fetched_data = cr.dictfetchall()
        elif data['levels'] == 'detailed':
            state = """ WHERE am.state = 'posted' """ if data[
                                                             'target_move'] == 'posted' else ''
            query1 = """SELECT aa.id,aa.name,aa.code, sum(aml.debit) AS total_debit,
                        sum(aml.credit) AS total_credit,sum(
                        aml.balance) AS total_balance FROM (
                        SELECT am.id, am.state FROM account_move as am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         WHERE am.date BETWEEN '""" + str(
                data['date_from']) + """' and '""" + str(
                data['date_to']) + """' ) am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         """ + state + """GROUP BY aa.id,aa.name, aa.code"""
            cr = self._cr
            cr.execute(query1)
            fetched_data = cr.dictfetchall()
            for account in self.env['account.account'].search([]):
                child_lines = self._get_journal_lines(account, data)
                if child_lines:
                    journal_res.append(child_lines)
        else:
            state = """AND am.state = 'posted' """ if data[
                                                          'target_move'] == 'posted' else ''
            sql = """SELECT DISTINCT aa.name,aa.code, sum(
                    aml.debit) AS total_debit,
                     sum(aml.credit) AS total_credit FROM (
                     SELECT am.* FROM account_move as am
                     LEFT JOIN account_move_line aml ON aml.move_id = am.id
                     LEFT JOIN account_account aa ON aa.id = aml.account_id
                     WHERE am.date BETWEEN '""" + str(
                data['date_from']) + """' and '""" + str(
                data['date_to']) + """' """ + state + """) am
                     LEFT JOIN account_move_line aml ON aml.move_id = am.id
                     LEFT JOIN account_account aa ON aa.id = aml.account_id
                     GROUP BY aa.name, aa.code"""
            cr = self._cr
            cr.execute(sql)
            fetched = cr.dictfetchall()
            for account in self.env['account.account'].search([]):
                child_lines = self._get_lines(account, data)
                if child_lines:
                    account_res.append(child_lines)

        logged_users = self.env['res.company']._company_default_get(
            'account.account')
        sheet = workbook.add_worksheet()
        bold = workbook.add_format({'align': 'center',
                                    'bold': True,
                                    'font_size': '10px',
                                    'border': 1})
        date = workbook.add_format({'font_size': '10px'})
        cell_format = workbook.add_format({'bold': True,
                                           'font_size': '10px'})
        head = workbook.add_format({'align': 'center',
                                    'bold': True,
                                    'bg_color': '#D3D3D3',
                                    'font_size': '15px'})
        txt = workbook.add_format({'align': 'left',
                                   'font_size': '10px'})
        txt_left = workbook.add_format({'align': 'left',
                                        'font_size': '10px',
                                        'border': 1})
        txt_center = workbook.add_format({'align': 'center',
                                          'font_size': '10px',
                                          'border': 1})
        amount = workbook.add_format({'align': 'right',
                                      'font_size': '10px',
                                      'border': 1})
        amount_bold = workbook.add_format({'align': 'right',
                                           'bold': True,
                                           'font_size': '10px',
                                           'border': 1})
        txt_bold = workbook.add_format({'align': 'left',
                                        'bold': True,
                                        'font_size': '10px',
                                        'border': 1})

        sheet.set_column('C:C', 30, cell_format)
        sheet.set_column('D:E', 20, cell_format)
        sheet.set_column('F:F', 20, cell_format)
        sheet.write('C2', "Report Date", txt)
        sheet.write('D2', str(data['today']), txt)
        sheet.write('F2', logged_users.name, txt)
        sheet.merge_range('C3:F4', 'CASH FLOW STATEMENTS', head)

        if data['target_move'] == 'posted':
            sheet.write('C6', "Target Moves :", cell_format)
            sheet.write('C7', 'All Posted Entries', date)
        else:
            sheet.write('C6', "Target Moves :", cell_format)
            sheet.write('C7', 'All Entries', date)

        sheet.write('D6', "Date From", cell_format)
        sheet.write('E6', str(data['date_from']), date)
        sheet.write('D7', "Date To", cell_format)
        sheet.write('E7', str(data['date_to']), date)

        sheet.merge_range('C8:F8', '', head)
        sheet.write('C9', 'NAME', bold)
        sheet.write('D9', 'CASH IN', bold)
        sheet.write('E9', 'CASH OUT', bold)
        sheet.write('F9', 'BALANCE', bold)

        row_num = 8
        col_num = 2
        fetched_data_list = fetched_data.copy()
        account_res_list = account_res.copy()
        journal_res_list = journal_res.copy()
        fetched_list = fetched.copy()
        filtered_fetched_data_list = [entry for entry in fetched_data_list if
                                 None not in entry.values()]

        for i in filtered_fetched_data_list:
            if data['levels'] == 'summary':
                sheet.write(row_num + 1, col_num,
                            str(i['month_part']) + str(int(i['year_part'])),
                            txt_left)
                sheet.write(row_num + 1, col_num + 1,
                            '{:.2f} %'.format(i['total_debit']) + str(currency_symbol),
                            amount)
                sheet.write(row_num + 1, col_num + 2,
                            '{:.2f} %'.format(i['total_credit']) + str(currency_symbol),
                            amount)
                sheet.write(row_num + 1, col_num + 3,
                            '{:.2f} %'.format(i['total_debit'] - i['total_credit']) + str(
                                currency_symbol),
                            amount)
                row_num = row_num + 1
            elif data['levels'] == 'consolidated':
                acc = self.env['account.account'].browse(i['id'])
                sheet.write(row_num + 1, col_num, acc.name, txt_left)
                sheet.write(row_num + 1, col_num + 1,
                            '{:.2f} %'.format(i['total_debit']) + str(currency_symbol),
                            amount)
                sheet.write(row_num + 1, col_num + 2,
                            '{:.2f} %'.format(i['total_credit']) + str(currency_symbol),
                            amount)
                if i['total_credit'] and i['total_credit']:
                    sheet.write(row_num + 1, col_num + 3,
                                '{:.2f} %'.format(i['total_debit'] - i['total_credit']) + str(
                                    currency_symbol),
                                amount)
                else:
                    sheet.write(row_num + 1, col_num + 3,
                                str(0) + str(currency_symbol),
                                amount)
                row_num = row_num + 1

        for j in journal_res_list:
            for k in filtered_fetched_data_list:
                account_name = self.env['account.account'].browse(k['id'])
                if account_name.name == j['account']:
                    sheet.write(row_num + 1, col_num,
                                str(k['code']) + str(account_name.name),
                                txt_bold)
                    sheet.write(row_num + 1, col_num + 1,
                                '{:.2f} %'.format(k['total_debit']) + str(currency_symbol),
                                amount_bold)
                    sheet.write(row_num + 1, col_num + 2,
                                '{:.2f} %'.format(k['total_credit']) + str(currency_symbol),
                                amount_bold)
                    if k['total_debit'] and k['total_credit']:
                        sheet.write(row_num + 1, col_num + 3,
                                    '{:.2f} %'.format(k['total_debit'] - k[
                                        'total_credit']) + str(
                                        currency_symbol), amount_bold)
                    else:
                        sheet.write(row_num + 1, col_num + 3,
                                    str(0) + str(
                                        currency_symbol), amount_bold)
                    row_num = row_num + 1
            for l in j['journal_lines']:
                acc = self.env['account.account'].browse(l['id'])
                sheet.write(row_num + 1, col_num, acc.name, txt_left)
                sheet.write(row_num + 1, col_num + 1,
                            '{:.2f} %'.format(l['total_debit']) + str(currency_symbol),
                            amount)
                sheet.write(row_num + 1, col_num + 2,
                            '{:.2f} %'.format(l['total_credit']) + str(currency_symbol),
                            amount)
                sheet.write(row_num + 1, col_num + 3,
                            '{:.2f} %'.format(l['total_debit'] - l['total_credit']) + str(
                                currency_symbol),
                            amount)
                row_num = row_num + 1

        for j in account_res_list:
            for k in fetched_list:

                if k['name'] == j['account']:
                    sheet.write(row_num + 1, col_num,
                                str(k['code']) + str(k['name']), txt_bold)
                    sheet.write(row_num + 1, col_num + 1,
                                '{:.2f} %'.format(k['total_debit']) + str(currency_symbol),
                                amount_bold)
                    sheet.write(row_num + 1, col_num + 2,
                                '{:.2f} %'.format(k['total_credit']) + str(currency_symbol),
                                amount_bold)
                    sheet.write(row_num + 1, col_num + 3,
                                '{:.2f} %'.format(k['total_debit'] - k['total_credit']) + str(
                                    currency_symbol), amount_bold)
                    row_num = row_num + 1
            for l in j['journal_lines']:
                if l['account_name'] == j['account']:
                    sheet.write(row_num + 1, col_num, l['name'], txt_left)
                    sheet.write(row_num + 1, col_num + 1,
                                '{:.2f} %'.format(l['total_debit']) + str(currency_symbol),
                                amount)
                    sheet.write(row_num + 1, col_num + 2,
                                '{:.2f} %'.format(l['total_credit']) + str(currency_symbol),
                                amount)
                    sheet.write(row_num + 1, col_num + 3,
                                '{:.2f} %'.format(l['total_debit'] - l['total_credit']) + str(
                                    currency_symbol),
                                amount)
                    row_num = row_num + 1
                for m in j['move_lines']:
                    if m['name'] == l['name']:
                        sheet.write(row_num + 1, col_num, m['move_name'],
                                    txt_center)
                        sheet.write(row_num + 1, col_num + 1,
                                    '{:.2f} %'.format(m['total_debit']) + str(
                                        currency_symbol), amount)
                        sheet.write(row_num + 1, col_num + 2,
                                    '{:.2f} %'.format(m['total_credit']) + str(
                                        currency_symbol), amount)
                        sheet.write(row_num + 1, col_num + 3,
                                    '{:.2f} %'.format(m['total_debit'] - m[
                                        'total_credit']) + str(currency_symbol),
                                    amount)
                        row_num = row_num + 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def _get_lines(self, account, data):
        """ Fetch values for lines"""
        state = """AND am.state = 'posted' """ if data[
                                                      'target_move'] == 'posted' else ''
        query = """SELECT aml.account_id,aj.name, am.name as move_name, sum(
                    aml.debit) AS total_debit, 
                     sum(aml.credit) AS total_credit FROM (
                     SELECT am.* FROM account_move as am
                     LEFT JOIN account_move_line aml ON aml.move_id = am.id
                     LEFT JOIN account_account aa ON aa.id = aml.account_id
                     WHERE am.date BETWEEN '""" + str(
            data['date_from']) + """' and '""" + str(
            data['date_to']) + """'  """ + state + """) am
                     LEFT JOIN account_move_line aml ON aml.move_id = am.id
                     LEFT JOIN account_account aa ON aa.id = aml.account_id
                     LEFT JOIN account_journal aj ON aj.id = am.journal_id
                     WHERE aa.id = """ + str(account.id) + """
                     GROUP BY am.name, aml.account_id, aj.name"""

        cr = self._cr
        cr.execute(query)
        fetched_data = cr.dictfetchall()

        sql2 = """SELECT aa.name as account_name, aj.id, aj.name, sum(
                    aml.debit) AS total_debit,
                     sum(aml.credit) AS total_credit FROM (
                     SELECT am.* FROM account_move as am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         WHERE am.date BETWEEN '""" + str(
            data['date_from']) + """' and '""" + str(
            data['date_to']) + """'  """ + state + """) am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         LEFT JOIN account_journal aj ON aj.id = am.journal_id
                         WHERE aa.id = """ + str(account.id) + """
                         GROUP BY aa.name, aj.name, aj.id"""

        cr = self._cr
        cr.execute(sql2)
        fetch_data = cr.dictfetchall()
        if fetched_data:
            return {
                'account': account.name,
                'code': account.code,
                'move_lines': fetched_data,
                'journal_lines': fetch_data,
            }

    def _get_journal_lines(self, account, data):
        """ Fetch values based on journal and pass it in sublines"""
        state = """AND am.state = 'posted' """ if data[
                                                      'target_move'] == 'posted' else ''
        sql2 = """SELECT aa.id,aa.name as account_name, aj.id, aj.name, sum(
                    aml.debit) AS total_debit,
                     sum(aml.credit) AS total_credit FROM (
                     SELECT am.* FROM account_move as am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                    WHERE am.date BETWEEN '""" + str(
            data['date_from']) + """' and '""" + str(
            data['date_to']) + """' """ + state + """) am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         LEFT JOIN account_journal aj ON aj.id = am.journal_id
                         WHERE aa.id = """ + str(account.id) + """
                         GROUP BY aa.id,aa.name, aj.name, aj.id"""
        cr = self._cr
        cr.execute(sql2)
        fetched_data = cr.dictfetchall()
        if fetched_data:
            return {
                'account': account.name,
                'journal_lines': fetched_data,
            }
