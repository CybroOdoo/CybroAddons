# -*- coding: utf-8 -*-
#############################################################################
#
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
#############################################################################
import io
import json
import xlsxwriter
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import json_default


class AccountWizard(models.TransientModel):
    """This Transient model is used to create a wizard"""
    _name = "account.wizard"
    _description = 'Account Wizard'

    name = fields.Char(default="Invoice", help='Name of Invoice')
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
                                   'Consolidated: Based on accounts.\n'
                                   'Detailed: Based on accounts and journals.\n'
                                   'Very Detailed: Accounts with journals and their move lines')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True,
                                   default='posted', help='Type of entries')

    def generate_pdf_report(self):
        """ Generate the pdf reports and return values to template"""
        self.ensure_one()
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise UserError(_("Start date should be less than end date"))
        data = {
            'ids': self.ids,
            'model': self._name,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'levels': self.levels,
            'target_move': self.target_move,
            'today': self.today,
            'logged_users': self.env.user.name,
        }
        return self.env.ref(
            'advance_cash_flow_statements.pdf_report_action').report_action(
            self,
            data=data,
            config=False)

    def generate_xlsx_report(self):
        """ Generate xlsx report return values to template"""
        self.ensure_one()
        if self.date_from and self.date_to and self.date_from > self.date_to:
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
                     'options': json.dumps(data, default=json_default),
                     'report_name': 'Adv Cash Flow Statement',
                     },
        }

    def get_xlsx_report(self, data, response):
        """ Update the xlsx template and pass values to templates"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        company = self.env.company
        currency_symbol = (company.currency_id.symbol or '') + " "
        state_clause = "AND am.state = 'posted'" if data.get('target_move') == 'posted' else "AND am.state != 'cancel'"

        logged_user = self.env.user
        sheet = workbook.add_worksheet()
        bold = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 10, 'border': 1})
        date_format = workbook.add_format({'font_size': 10})
        cell_format = workbook.add_format({'bold': True, 'font_size': 10})
        head = workbook.add_format({'align': 'center', 'bold': True, 'bg_color': '#D3D3D3', 'font_size': 15})
        txt = workbook.add_format({'align': 'left', 'font_size': 10})
        txt_left = workbook.add_format({'align': 'left', 'font_size': 10, 'border': 1})
        txt_center = workbook.add_format({'align': 'center', 'font_size': 10, 'border': 1})
        amount = workbook.add_format({'align': 'right', 'font_size': 10, 'border': 1})
        amount_bold = workbook.add_format({'align': 'right', 'bold': True, 'font_size': 10, 'border': 1})
        txt_bold = workbook.add_format({'align': 'left', 'bold': True, 'font_size': 10, 'border': 1})

        sheet.set_column('C:C', 35, cell_format)
        sheet.set_column('D:E', 20, cell_format)
        sheet.set_column('F:F', 20, cell_format)
        sheet.write('C2', "Report Date", txt)
        sheet.write('D2', str(data.get('today', '')), txt)
        sheet.write('F2', logged_user.name, txt)
        sheet.merge_range('C3:F4', 'CASH FLOW STATEMENTS', head)

        target_move_label = 'All Posted Entries' if data.get('target_move') == 'posted' else 'All Entries'
        sheet.write('C6', "Target Moves :", cell_format)
        sheet.write('C7', target_move_label, date_format)

        sheet.write('D6', "Date From", cell_format)
        sheet.write('E6', str(data.get('date_from', '')), date_format)
        sheet.write('D7', "Date To", cell_format)
        sheet.write('E7', str(data.get('date_to', '')), date_format)

        sheet.merge_range('C8:F8', '', head)
        sheet.write('C9', 'NAME', bold)
        sheet.write('D9', 'CASH IN', bold)
        sheet.write('E9', 'CASH OUT', bold)
        sheet.write('F9', 'BALANCE', bold)

        row_num = 9
        col_num = 2

        if data['levels'] == 'summary':
            query = f"""
                SELECT 
                    to_char(am.date, 'Month') as month_part, 
                    EXTRACT(YEAR FROM am.date) as year_part,
                    SUM(aml.debit) AS total_debit, 
                    SUM(aml.credit) AS total_credit,
                    SUM(aml.balance) AS total_balance
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                WHERE am.date BETWEEN %s AND %s
                  AND am.company_id = %s
                  {state_clause}
                GROUP BY month_part, year_part
                ORDER BY year_part, min(am.date)
            """
            self.env.cr.execute(query, (data['date_from'], data['date_to'], company.id))
            fetched_data = self.env.cr.dictfetchall()
            for i in fetched_data:
                label = f"{i['month_part'].strip()} {int(i['year_part'])}"
                tot_debit = i['total_debit'] or 0.0
                tot_credit = i['total_credit'] or 0.0
                tot_balance = tot_debit - tot_credit
                sheet.write(row_num, col_num, label, txt_left)
                sheet.write(row_num, col_num + 1, f"{currency_symbol}{tot_debit:.2f}", amount)
                sheet.write(row_num, col_num + 2, f"{currency_symbol}{tot_credit:.2f}", amount)
                sheet.write(row_num, col_num + 3, f"{currency_symbol}{tot_balance:.2f}", amount)
                row_num += 1

        elif data['levels'] == 'consolidated':
            query = f"""
                SELECT 
                    aml.account_id,
                    SUM(aml.debit) AS total_debit, 
                    SUM(aml.credit) AS total_credit,
                    SUM(aml.balance) AS total_balance
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                WHERE am.date BETWEEN %s AND %s
                  AND am.company_id = %s
                  {state_clause}
                GROUP BY aml.account_id
            """
            self.env.cr.execute(query, (data['date_from'], data['date_to'], company.id))
            fetched_data = self.env.cr.dictfetchall()
            for i in fetched_data:
                account = self.env['account.account'].browse(i['account_id'])
                code = account.code or ''
                name = account.name or ''
                acc_label = f"{code} {name}".strip() if code else name
                tot_debit = i['total_debit'] or 0.0
                tot_credit = i['total_credit'] or 0.0
                tot_balance = tot_debit - tot_credit
                sheet.write(row_num, col_num, acc_label, txt_left)
                sheet.write(row_num, col_num + 1, f"{currency_symbol}{tot_debit:.2f}", amount)
                sheet.write(row_num, col_num + 2, f"{currency_symbol}{tot_credit:.2f}", amount)
                sheet.write(row_num, col_num + 3, f"{currency_symbol}{tot_balance:.2f}", amount)
                row_num += 1

        elif data['levels'] == 'detailed':
            query = f"""
                SELECT 
                    aml.account_id,
                    SUM(aml.debit) AS total_debit, 
                    SUM(aml.credit) AS total_credit,
                    SUM(aml.balance) AS total_balance
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                WHERE am.date BETWEEN %s AND %s
                  AND am.company_id = %s
                  {state_clause}
                GROUP BY aml.account_id
            """
            self.env.cr.execute(query, (data['date_from'], data['date_to'], company.id))
            fetched_data = self.env.cr.dictfetchall()
            for i in fetched_data:
                account = self.env['account.account'].browse(i['account_id'])
                code = account.code or ''
                name = account.name or ''
                acc_label = f"{code} {name}".strip() if code else name
                tot_debit = i['total_debit'] or 0.0
                tot_credit = i['total_credit'] or 0.0
                tot_balance = tot_debit - tot_credit

                sheet.write(row_num, col_num, acc_label, txt_bold)
                sheet.write(row_num, col_num + 1, f"{currency_symbol}{tot_debit:.2f}", amount_bold)
                sheet.write(row_num, col_num + 2, f"{currency_symbol}{tot_credit:.2f}", amount_bold)
                sheet.write(row_num, col_num + 3, f"{currency_symbol}{tot_balance:.2f}", amount_bold)
                row_num += 1

                journal_lines = self._get_journal_lines(account, data)
                for jl in journal_lines:
                    j_debit = jl['total_debit'] or 0.0
                    j_credit = jl['total_credit'] or 0.0
                    j_balance = j_debit - j_credit
                    sheet.write(row_num, col_num, f"    {jl['name']}", txt_left)
                    sheet.write(row_num, col_num + 1, f"{currency_symbol}{j_debit:.2f}", amount)
                    sheet.write(row_num, col_num + 2, f"{currency_symbol}{j_credit:.2f}", amount)
                    sheet.write(row_num, col_num + 3, f"{currency_symbol}{j_balance:.2f}", amount)
                    row_num += 1

        else:  # very detailed
            query = f"""
                SELECT 
                    aml.account_id,
                    SUM(aml.debit) AS total_debit, 
                    SUM(aml.credit) AS total_credit,
                    SUM(aml.balance) AS total_balance
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                WHERE am.date BETWEEN %s AND %s
                  AND am.company_id = %s
                  {state_clause}
                GROUP BY aml.account_id
            """
            self.env.cr.execute(query, (data['date_from'], data['date_to'], company.id))
            fetched = self.env.cr.dictfetchall()
            for i in fetched:
                account = self.env['account.account'].browse(i['account_id'])
                code = account.code or ''
                name = account.name or ''
                acc_label = f"{code} {name}".strip() if code else name
                tot_debit = i['total_debit'] or 0.0
                tot_credit = i['total_credit'] or 0.0
                tot_balance = tot_debit - tot_credit

                sheet.write(row_num, col_num, acc_label, txt_bold)
                sheet.write(row_num, col_num + 1, f"{currency_symbol}{tot_debit:.2f}", amount_bold)
                sheet.write(row_num, col_num + 2, f"{currency_symbol}{tot_credit:.2f}", amount_bold)
                sheet.write(row_num, col_num + 3, f"{currency_symbol}{tot_balance:.2f}", amount_bold)
                row_num += 1

                lines_data = self._get_lines(account, data)
                if lines_data:
                    for jl in lines_data.get('journal_lines', []):
                        j_debit = jl['total_debit'] or 0.0
                        j_credit = jl['total_credit'] or 0.0
                        j_balance = j_debit - j_credit
                        sheet.write(row_num, col_num, f"    {jl['name']}", txt_left)
                        sheet.write(row_num, col_num + 1, f"{currency_symbol}{j_debit:.2f}", amount)
                        sheet.write(row_num, col_num + 2, f"{currency_symbol}{j_credit:.2f}", amount)
                        sheet.write(row_num, col_num + 3, f"{currency_symbol}{j_balance:.2f}", amount)
                        row_num += 1

                        for ml in lines_data.get('move_lines', []):
                            if ml.get('journal_id') == jl.get('id'):
                                m_debit = ml['total_debit'] or 0.0
                                m_credit = ml['total_credit'] or 0.0
                                m_balance = m_debit - m_credit
                                sheet.write(row_num, col_num, f"        {ml['move_name']}", txt_center)
                                sheet.write(row_num, col_num + 1, f"{currency_symbol}{m_debit:.2f}", amount)
                                sheet.write(row_num, col_num + 2, f"{currency_symbol}{m_credit:.2f}", amount)
                                sheet.write(row_num, col_num + 3, f"{currency_symbol}{m_balance:.2f}", amount)
                                row_num += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def _get_lines(self, account, data):
        """ Fetch move line and journal totals for a specific account."""
        company = self.env.company
        state_clause = "AND am.state = 'posted'" if data.get('target_move') == 'posted' else "AND am.state != 'cancel'"

        # Move line totals
        query_moves = f"""
            SELECT 
                aml.account_id,
                am.journal_id,
                am.name as move_name, 
                SUM(aml.debit) AS total_debit, 
                SUM(aml.credit) AS total_credit
            FROM account_move_line aml
            JOIN account_move am ON aml.move_id = am.id
            WHERE am.date BETWEEN %s AND %s
              AND am.company_id = %s
              {state_clause}
              AND aml.account_id = %s
            GROUP BY am.name, aml.account_id, am.journal_id
        """
        self.env.cr.execute(query_moves, (data['date_from'], data['date_to'], company.id, account.id))
        move_lines = self.env.cr.dictfetchall()

        # Journal totals for this account
        query_journals = f"""
            SELECT 
                aj.id as journal_id, 
                SUM(aml.debit) AS total_debit, 
                SUM(aml.credit) AS total_credit
            FROM account_move_line aml
            JOIN account_move am ON aml.move_id = am.id
            JOIN account_journal aj ON aj.id = am.journal_id
            WHERE am.date BETWEEN %s AND %s
              AND am.company_id = %s
              {state_clause}
              AND aml.account_id = %s
            GROUP BY aj.id
        """
        self.env.cr.execute(query_journals, (data['date_from'], data['date_to'], company.id, account.id))
        journal_records = self.env.cr.dictfetchall()

        journal_lines = []
        for jr in journal_records:
            journal = self.env['account.journal'].browse(jr['journal_id'])
            journal_lines.append({
                'id': journal.id,
                'name': journal.name,
                'total_debit': jr['total_debit'],
                'total_credit': jr['total_credit'],
            })

        if move_lines:
            return {
                'account_id': account.id,
                'account': account.name,
                'code': account.code or '',
                'move_lines': move_lines,
                'journal_lines': journal_lines,
            }
        return {}

    def _get_journal_lines(self, account, data):
        """ Fetch journal totals for a specific account."""
        company = self.env.company
        state_clause = "AND am.state = 'posted'" if data.get('target_move') == 'posted' else "AND am.state != 'cancel'"

        query = f"""
            SELECT 
                aj.id as journal_id, 
                SUM(aml.debit) AS total_debit, 
                SUM(aml.credit) AS total_credit
            FROM account_move_line aml
            JOIN account_move am ON aml.move_id = am.id
            JOIN account_journal aj ON aj.id = am.journal_id
            WHERE am.date BETWEEN %s AND %s
              AND am.company_id = %s
              {state_clause}
              AND aml.account_id = %s
            GROUP BY aj.id
        """
        self.env.cr.execute(query, (data['date_from'], data['date_to'], company.id, account.id))
        records = self.env.cr.dictfetchall()

        result = []
        for r in records:
            journal = self.env['account.journal'].browse(r['journal_id'])
            result.append({
                'id': journal.id,
                'name': journal.name,
                'total_debit': r['total_debit'],
                'total_credit': r['total_credit'],
            })
        return result
