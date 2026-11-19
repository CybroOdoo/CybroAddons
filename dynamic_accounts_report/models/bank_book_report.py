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
from dateutil.relativedelta import relativedelta
import xlsxwriter
from datetime import datetime
from odoo.tools import date_utils
from odoo import api, fields, models


class BankBookReport(models.TransientModel):
    """For creating Bank Book report."""
    _name = 'bank.book.report'
    _description = 'Account Bank Book Report'

    @api.model
    def view_report(self):
        """
        This method retrieves and returns the necessary data for the bank book
        report. It fetches account move lines, grouped by accounts, and
        calculates total debit and credit amounts. The resulting data includes
        move lines for each account and the total debit and credit amounts for
        each account.
        """
        data = {}
        move_lines_total = {}
        journals = self.env['account.journal'].search(
            [('type', '=', 'bank')])
        account_move_lines = self.env['account.move.line'].search(
            [('parent_state', '=', 'posted'),
             ('journal_id', 'in', journals.ids)])
        bank_accounts = journals.default_account_id | self.env[
            'account.account'].search(
            [('account_type', 'in', ['asset_cash', 'liability_credit_card'])])
        if account_move_lines:
            bank_accounts |= account_move_lines.mapped('account_id')
        accounts = bank_accounts.read(['display_name', 'name'])
        currency_id = self.env.company.currency_id.symbol
        data['currency'] = currency_id
        for account in accounts:
            move_lines = account_move_lines.filtered(
                lambda x: x.account_id.id == account['id'])
            if not move_lines:
                continue
            move_line_data = move_lines.read(
                ['date', 'journal_id', 'partner_id', 'move_name', 'debit',
                 'move_id',
                 'credit', 'name', 'ref'])
            account_name = account.get('display_name') or account.get('name')
            data[account_name] = move_line_data
            move_lines_total[account_name] = {
                'total_debit': round(sum(move_lines.mapped('debit')), 2),
                'total_credit': round(sum(move_lines.mapped('credit')), 2),
                'currency_id': currency_id}
        data['move_lines_total'] = move_lines_total
        data['accounts'] = accounts
        return data

    @api.model
    def get_filter_values(self, partner_id=None, data_range=None,
                          account_list=None, options=None):
        if isinstance(account_list, dict) and (
            options is None or isinstance(options, list)
        ):
            account_list, options = options, account_list
        """
        Retrieve filtered data for the partner ledger report.
        Args:
            partner_id (list or None): List of partner IDs for filtering by
                                       partner. If None, all partners will be
                                       included.
            data_range (str or dict): Range of data to filter the account move
                                      lines. Can be a string ('month', 'year',
                                      'quarter','last-month', 'last-year',
                                      'last-quarter') or a dictionary with
                                      'start_date' and 'end_date'.
            account_list (list or None): List of account IDs for filtering by
                                         account. If None, all accounts will be
                                         included.
            options (dict or None): Additional filtering options with 'draft'
                                    key (boolean) to include draft moves if
                                    True.
        Returns:
            dict: Filtered data for the partner ledger report, grouped by
                  accounts and summary of total debit and credit amounts.
        """
        data = {}
        move_lines_total = {}
        today = fields.Date.today()
        quarter_start, quarter_end = date_utils.get_quarter(today)
        previous_quarter_start = quarter_start - relativedelta(months=3)
        previous_quarter_end = quarter_start - relativedelta(days=1)
        journals = self.env['account.journal'].search([('type', '=', 'bank')])
        if options and options.get('draft'):
            option_domain = ['posted', 'draft']
        else:
            option_domain = ['posted']
        domain = [('parent_state', 'in', option_domain),
                  ('journal_id', 'in', journals.ids)]
        if partner_id:
            domain.append(('partner_id', 'in', partner_id))
        if account_list:
            resolved_account_ids = []
            for a in account_list:
                if isinstance(a, int):
                    resolved_account_ids.append(a)
                elif isinstance(a, str):
                    if a.isdigit():
                        resolved_account_ids.append(int(a))
                    else:
                        acc = self.env['account.account'].search(
                            [('name', '=', a)], limit=1)
                        if acc:
                            resolved_account_ids.append(acc.id)
            if resolved_account_ids:
                domain.append(('account_id', 'in', resolved_account_ids))
            else:
                domain.append(('account_id', 'in', []))
        if data_range:
            if isinstance(data_range, str):
                if data_range == 'month':
                    month_start, month_end = date_utils.get_month(today)
                    domain += [('date', '>=', month_start),
                               ('date', '<=', month_end)]
                elif data_range == 'year':
                    year_start, year_end = date_utils.get_fiscal_year(today)
                    domain += [('date', '>=', year_start),
                               ('date', '<=', year_end)]
                elif data_range == 'quarter':
                    domain += [('date', '>=', quarter_start),
                               ('date', '<=', quarter_end)]
                elif data_range == 'last-month':
                    last_month_start, last_month_end = date_utils.get_month(
                        today - relativedelta(months=1))
                    domain += [('date', '>=', last_month_start),
                               ('date', '<=', last_month_end)]
                elif data_range == 'last-year':
                    last_year_start, last_year_end = date_utils.get_fiscal_year(
                        today - relativedelta(years=1))
                    domain += [('date', '>=', last_year_start),
                               ('date', '<=', last_year_end)]
                elif data_range == 'last-quarter':
                    domain += [('date', '>=', previous_quarter_start),
                               ('date', '<=', previous_quarter_end)]
            elif isinstance(data_range, dict):
                start = data_range.get('start_date')
                end = data_range.get('end_date')
                if start and end:
                    start_date = datetime.strptime(start, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end, '%Y-%m-%d').date()
                    domain += [('date', '>=', start_date),
                               ('date', '<=', end_date)]
                elif start:
                    start_date = datetime.strptime(start, '%Y-%m-%d').date()
                    domain += [('date', '>=', start_date)]
                elif end:
                    end_date = datetime.strptime(end, '%Y-%m-%d').date()
                    domain += [('date', '<=', end_date)]
        account_move_lines = self.env['account.move.line'].search(domain)
        bank_accounts = journals.default_account_id | self.env[
            'account.account'].search(
            [('account_type', 'in', ['asset_cash', 'liability_credit_card'])])
        if account_move_lines:
            bank_accounts |= account_move_lines.mapped('account_id')
        accounts = bank_accounts.read(['display_name', 'name'])
        currency_id = self.env.company.currency_id.symbol
        data['currency'] = currency_id
        for account in accounts:
            move_lines = account_move_lines.filtered(
                lambda x: x.account_id.id == account['id'])
            if not move_lines:
                continue
            move_line_data = move_lines.read(
                ['date', 'journal_id', 'partner_id', 'move_name', 'debit',
                 'move_id',
                 'credit', 'name', 'ref'])
            account_name = account.get('display_name') or account.get('name')
            data[account_name] = move_line_data
            move_lines_total[account_name] = {
                'total_debit': round(sum(move_lines.mapped('debit')), 2),
                'total_credit': round(sum(move_lines.mapped('credit')), 2),
                'currency_id': currency_id}
        data['move_lines_total'] = move_lines_total
        data['accounts'] = accounts
        return data

    @api.model
    def get_xlsx_report(self, data, response, report_name, report_action):
        """
        Generate an Excel report based on the provided data.
        :param data: The data used to generate the report.
        :type data: str (JSON format)
        :param response: The response object to write the report to.
        :type response: object
        :param report_name: The name of the report.
        :type report_name: str
        :return: None
        """
        data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        start_date = data['filters']['start_date'] if \
            data['filters']['start_date'] else ''
        end_date = data['filters']['end_date'] if \
            data['filters']['end_date'] else ''
        sheet = workbook.add_worksheet()
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '15px'})
        sub_heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1, 'bg_color': '#D3D3D3',
             'border_color': 'black'})
        filter_head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1, 'bg_color': '#D3D3D3',
             'border_color': 'black'})
        filter_body = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px'})
        side_heading_sub = workbook.add_format(
            {'align': 'left', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        side_heading_sub.set_indent(1)
        txt_name = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_name.set_indent(2)
        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        col = 0
        sheet.write('A1:b1', report_name, head)
        sheet.write('B3:b4', 'Date Range', filter_head)
        sheet.write('B4:b4', 'Partners', filter_head)
        sheet.write('B5:b4', 'Accounts', filter_head)
        sheet.write('B6:b4', 'Options', filter_head)
        if start_date or end_date:
            sheet.merge_range('C3:G3', f"{start_date} to {end_date}",
                              filter_body)
        if data['filters']['partner']:
            display_names = [partner.get('display_name', 'undefined') for
                             partner in data['filters']['partner']]
            display_names_str = ', '.join(display_names)
            sheet.merge_range('C4:G4', display_names_str, filter_body)
        if data['filters']['account']:
            account_keys_str = ', '.join(data['filters']['account'])
            sheet.merge_range('C5:G5', account_keys_str, filter_body)
        if data['filters']['options']:
            option_keys = list(data['filters']['options'].keys())
            option_keys_str = ', '.join(option_keys)
            sheet.merge_range('C6:G6', option_keys_str, filter_body)
        if data:
            if report_action == 'dynamic_accounts_report.action_bank_book':
                sheet.write(8, col, ' ', sub_heading)
                sheet.merge_range('B9:C9', 'Journal', sub_heading)
                sheet.merge_range('D9:E9', 'Partner', sub_heading)
                sheet.merge_range('F9:G9', 'Ref', sub_heading)
                sheet.merge_range('H9:I9', 'Move', sub_heading)
                sheet.merge_range('J9:K9', 'Entry Label', sub_heading)
                sheet.merge_range('L9:M9', 'Debit', sub_heading)
                sheet.merge_range('N9:O9', 'Credit', sub_heading)
                sheet.merge_range('P9:Q9', 'Balance', sub_heading)
                row = 8
                for move_line in data['move_lines']:
                    row += 1
                    sheet.write(row, col, move_line, txt_name)
                    sheet.merge_range(row, col + 1, row, col + 2, ' ',
                                      txt_name)
                    sheet.merge_range(row, col + 3, row, col + 4, ' ',
                                      txt_name)
                    sheet.merge_range(row, col + 5, row, col + 6, ' ',
                                      txt_name)
                    sheet.merge_range(row, col + 7, row, col + 8, ' ',
                                      txt_name)
                    sheet.merge_range(row, col + 9, row, col + 10, ' ',
                                      txt_name)
                    sheet.merge_range(row, col + 11, row, col + 12,
                                      data['total'][move_line]['total_debit'],
                                      txt_name)
                    sheet.merge_range(row, col + 13, row, col + 14,
                                      data['total'][move_line]['total_credit'],
                                      txt_name)
                    sheet.merge_range(row, col + 15, row, col + 16,
                                      data['total'][move_line]['total_debit'] -
                                      data['total'][move_line]['total_credit'],
                                      txt_name)
                    for rec in data['data'][move_line]:
                        row += 1
                        if rec['partner_id']:
                            partner = rec['partner_id'][1]
                        else:
                            partner = ' '
                        sheet.write(row, col, rec['date'], txt_name)
                        sheet.merge_range(row, col + 1, row, col + 2,
                                          rec['journal_id'][1],
                                          txt_name)
                        sheet.merge_range(row, col + 3, row, col + 4, partner,
                                          txt_name)
                        sheet.merge_range(row, col + 5, row, col + 6,
                                          rec['ref'], txt_name)
                        sheet.merge_range(row, col + 7, row, col + 8,
                                          rec['move_name'],
                                          txt_name)
                        sheet.merge_range(row, col + 9, row, col + 10,
                                          rec['name'],
                                          txt_name)
                        sheet.merge_range(row, col + 11, row, col + 12,
                                          rec['debit_display'], txt_name)
                        sheet.merge_range(row, col + 13, row, col + 14,
                                          rec['credit_display'], txt_name)
                        sheet.merge_range(row, col + 15, row, col + 16, ' ',
                                          txt_name)
                sheet.merge_range(row + 1, col, row + 1, col + 10, 'Total',
                                  filter_head)
                sheet.merge_range(row + 1, col + 11, row + 1, col + 12,
                                  data['grand_total']['total_debit_display'],
                                  filter_head)
                sheet.merge_range(row + 1, col + 13, row + 1, col + 14,
                                  data['grand_total']['total_credit_display'],
                                  filter_head)
                sheet.merge_range(row + 1, col + 15, row + 1, col + 16,
                                  float(data['grand_total']['total_debit']) -
                                  float(data['grand_total']['total_credit']),
                                  filter_head)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
