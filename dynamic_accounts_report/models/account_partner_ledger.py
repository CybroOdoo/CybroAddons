# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
import io
import json
from dateutil.relativedelta import relativedelta
import xlsxwriter
from odoo import api, fields, models
from datetime import datetime
from odoo.tools import date_utils


class AccountPartnerLedger(models.TransientModel):
    """For creating Partner Ledger report"""
    _name = 'account.partner.ledger'
    _description = 'Partner Ledger Report'

    @api.model
    def view_report(self, option, tag):
        """
        Retrieve partner-related data for generating a report.

        :param option: The option for filtering the data.
        :type option: str

        :param tag: The tag used for filtering the data.
        :type tag: str

        :return: A dictionary containing the partner data for the report.
        :rtype: dict
        """
        partner_dict = {}
        partner_totals = {}
        move_line_ids = self.env['account.move.line'].search(
            [('account_type', 'in',
              ['liability_payable', 'asset_receivable']),
             ('parent_state', '=', 'posted')])
        partner_ids = move_line_ids.mapped('partner_id')
        for partner in partner_ids:
            move_line_id = move_line_ids.filtered(
                lambda x: x.partner_id == partner)
            move_line_list = []
            for move_line in move_line_id:
                move_line_data = move_line.read(
                    ['date', 'move_name', 'account_type', 'debit', 'credit',
                     'date_maturity', 'account_id', 'journal_id', 'move_id',
                     'matching_number', 'amount_currency'])
                account_code = self.env['account.account'].browse(
                    move_line.account_id.id).code
                journal_code = self.env['account.journal'].browse(
                    move_line.journal_id.id).code
                if account_code:
                    move_line_data[0]['jrnl'] = journal_code
                    move_line_data[0]['code'] = account_code
                move_line_list.append(move_line_data)
            partner_dict[partner.name] = move_line_list
            currency_id = self.env.company.currency_id.symbol
            partner_totals[partner.name] = {
                'total_debit': round(sum(move_line_id.mapped('debit')), 2),
                'total_credit': round(sum(move_line_id.mapped('credit')), 2),
                'currency_id': currency_id,
                'partner_id': partner.id}
            partner_dict['partner_totals'] = partner_totals
        return partner_dict

    @api.model
    def get_filter_values(self, partner_id, data_range, account, options):
        """
        Retrieve filtered partner-related data for generating a report.

        :param partner_id: The ID(s) of the partner(s) to filter by.
        :type partner_id: list or int

        :param data_range: The date range option for filtering the data.
        :type data_range: str

        :param account: The account type(s) to filter by.
        :type account: list or str

        :param options: Additional options for filtering the data.
        :type options: dict

        :return: A dictionary containing the filtered partner data.
        :rtype: dict
        """
        if options == {}:
            options = None
        if account == {}:
            account = None
        account_type_domain = []
        if options is None:
            option_domain = ['posted']
        elif 'draft' in options:
            option_domain = ['posted', 'draft']
        if account is None or (
                'Receivable' in account and 'Payable' in account):
            account_type_domain.append('liability_payable')
            account_type_domain.append('asset_receivable')
        elif 'Receivable' in account:
            account_type_domain.append('asset_receivable')
        elif 'Payable' in account:
            account_type_domain.append('liability_payable')
        partner_dict = {}
        partner_totals = {}
        today = fields.Date.today()
        quarter_start, quarter_end = date_utils.get_quarter(today)
        previous_quarter_start = quarter_start - relativedelta(months=3)
        previous_quarter_end = quarter_start - relativedelta(days=1)
        if not partner_id:
            partner_id = self.env['account.move.line'].search([(
                'account_type', 'in', account_type_domain),
                ('parent_state', 'in', option_domain)]).mapped(
                'partner_id').ids
        for partners in partner_id:
            partner = self.env['res.partner'].browse(partners).name
            if data_range:
                if data_range == 'month':
                    move_line_ids = self.env['account.move.line'].search(
                        [('partner_id', '=', partners), (
                            'account_type', 'in',
                            account_type_domain),
                         ('parent_state', 'in', option_domain)]).filtered(
                        lambda x: x.date.month == fields.Date.today().month)
                elif data_range == 'year':
                    move_line_ids = self.env['account.move.line'].search(
                        [('partner_id', '=', partners), (
                            'account_type', 'in',
                            account_type_domain),
                         ('parent_state', 'in', option_domain)]).filtered(
                        lambda x: x.date.year == fields.Date.today().year)
                elif data_range == 'quarter':
                    move_line_ids = self.env['account.move.line'].search(
                        [('partner_id', '=', partners), (
                            'account_type', 'in',
                            account_type_domain),
                         ('date', '>=', quarter_start),
                         ('date', '<=', quarter_end),
                         ('parent_state', 'in', option_domain)])
                elif data_range == 'last-month':
                    move_line_ids = self.env['account.move.line'].search(
                        [('partner_id', '=', partners), (
                            'account_type', 'in',
                            account_type_domain),
                         ('parent_state', 'in', option_domain)]).filtered(
                        lambda x: x.date.month == fields.Date.today().month - 1)
                elif data_range == 'last-year':
                    move_line_ids = self.env['account.move.line'].search(
                        [('partner_id', '=', partners), (
                            'account_type', 'in',
                            account_type_domain),
                         ('parent_state', 'in', option_domain)]).filtered(
                        lambda x: x.date.year == fields.Date.today().year - 1)
                elif data_range == 'last-quarter':
                    move_line_ids = self.env['account.move.line'].search(
                        [('partner_id', '=', partners), (
                            'account_type', 'in',
                            account_type_domain),
                         ('date', '>=', previous_quarter_start),
                         ('date', '<=', previous_quarter_end),
                         ('parent_state', 'in', option_domain)])
                elif 'start_date' in data_range and 'end_date' in data_range:
                    start_date = datetime.strptime(data_range['start_date'],
                                                   '%Y-%m-%d').date()
                    end_date = datetime.strptime(data_range['end_date'],
                                                 '%Y-%m-%d').date()
                    move_line_ids = self.env['account.move.line'].search(
                        [('partner_id', '=', partners), (
                            'account_type', 'in',
                            account_type_domain),
                         ('date', '>=', start_date),
                         ('date', '<=', end_date),
                         ('parent_state', 'in', option_domain)])
                elif 'start_date' in data_range:
                    start_date = datetime.strptime(data_range['start_date'],
                                                   '%Y-%m-%d').date()
                    move_line_ids = self.env['account.move.line'].search(
                        [('partner_id', '=', partners), (
                            'account_type', 'in',
                            account_type_domain),
                         ('date', '>=', start_date),
                         ('parent_state', 'in', option_domain)])
                elif 'end_date' in data_range:
                    end_date = datetime.strptime(data_range['end_date'],
                                                 '%Y-%m-%d').date()
                    move_line_ids = self.env['account.move.line'].search(
                        [('partner_id', '=', partners), (
                            'account_type', 'in',
                            account_type_domain),
                         ('date', '<=', end_date),
                         ('parent_state', 'in', option_domain)])
            else:
                move_line_ids = self.env['account.move.line'].search(
                    [('partner_id', '=', partners), (
                        'account_type', 'in',
                        account_type_domain),
                     ('parent_state', 'in', option_domain)])
            move_line_list = []
            for move_line in move_line_ids:
                move_line_data = move_line.read(
                    ['date', 'move_name', 'account_type', 'debit', 'credit',
                     'date_maturity', 'account_id', 'journal_id', 'move_id',
                     'matching_number', 'amount_currency'])
                account_code = self.env['account.account'].browse(
                    move_line.account_id.id).code
                journal_code = self.env['account.journal'].browse(
                    move_line.journal_id.id).code
                if account_code:
                    move_line_data[0]['jrnl'] = journal_code
                    move_line_data[0]['code'] = account_code
                move_line_list.append(move_line_data)
            partner_dict[partner] = move_line_list
            currency_id = self.env.company.currency_id.symbol
            partner_totals[partner] = {
                'total_debit': round(sum(move_line_ids.mapped('debit')), 2),
                'total_credit': round(sum(move_line_ids.mapped('credit')), 2),
                'currency_id': currency_id,
                'partner_id': partners}
            partner_dict['partner_totals'] = partner_totals
        return partner_dict

    @api.model
    def get_xlsx_report(self, data, response, report_name):
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
            {'font_size': 15, 'align': 'center', 'bold': True})
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
            account_keys = list(data['filters']['account'].keys())
            account_keys_str = ', '.join(account_keys)
            sheet.merge_range('C5:G5', account_keys_str, filter_body)
        if data['filters']['options']:
            option_keys = list(data['filters']['options'].keys())
            option_keys_str = ', '.join(option_keys)
            sheet.merge_range('C6:G6', option_keys_str, filter_body)
        if data:
            if report_name == 'Partner Ledger':
                sheet.write(8, col, ' ', sub_heading)
                sheet.write(8, col + 1, 'JNRL', sub_heading)
                sheet.write(8, col + 2, 'Account', sub_heading)
                sheet.merge_range('D9:E9', 'Ref', sub_heading)
                sheet.merge_range('F9:G9', 'Due Date', sub_heading)
                sheet.merge_range('H9:I9', 'Debit', sub_heading)
                sheet.merge_range('J9:K9', 'Credit', sub_heading)
                sheet.merge_range('L9:M9', 'Balance', sub_heading)
                row = 8
                for partner in data['partners']:
                    row += 1
                    sheet.write(row, col, partner, txt_name)
                    sheet.write(row, col + 1, ' ', txt_name)
                    sheet.write(row, col + 2, ' ', txt_name)
                    sheet.merge_range(row, col + 3, row, col + 4, ' ',
                                      txt_name)
                    sheet.merge_range(row, col + 5, row, col + 6, ' ',
                                      txt_name)
                    sheet.merge_range(row, col + 7, row, col + 8,
                                      data['total'][partner]['total_debit'],
                                      txt_name)
                    sheet.merge_range(row, col + 9, row, col + 10,
                                      data['total'][partner]['total_credit'],
                                      txt_name)
                    sheet.merge_range(row, col + 11, row, col + 12,
                                      data['total'][partner]['total_debit'] -
                                      data['total'][partner]['total_credit'],
                                      txt_name)
                    for rec in data['data'][partner]:
                        row += 1
                        sheet.write(row, col, rec[0]['date'], txt_name)
                        sheet.write(row, col + 1, rec[0]['jrnl'], txt_name)
                        sheet.write(row, col + 2, rec[0]['code'], txt_name)
                        sheet.merge_range(row, col + 3, row, col + 4,
                                          rec[0]['move_name'],
                                          txt_name)
                        sheet.merge_range(row, col + 5, row, col + 6,
                                          rec[0]['date_maturity'],
                                          txt_name)
                        sheet.merge_range(row, col + 7, row, col + 8,
                                          rec[0]['debit'], txt_name)
                        sheet.merge_range(row, col + 9, row, col + 10,
                                          rec[0]['credit'], txt_name)
                        sheet.merge_range(row, col + 11, row, col + 12, ' ',
                                          txt_name)
                row += 1
                sheet.merge_range(row, col, row, col + 6, 'Total', filter_head)
                sheet.merge_range(row, col + 7, row, col + 8,
                                  data['grand_total']['total_debit'],
                                  filter_head)
                sheet.merge_range(row, col + 9, row, col + 10,
                                  data['grand_total']['total_credit'],
                                  filter_head)
                sheet.merge_range(row, col + 11, row, col + 12,
                                  data['grand_total']['total_debit'] -
                                  data['grand_total']['total_credit'],
                                  filter_head)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
