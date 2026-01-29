# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import json
import xlsxwriter
from odoo import models
from odoo.tools import date_utils


class AccountMove(models.Model):
    """ Added function for printing excel report
            which is coming from a server action """
    _inherit = "account.move"

    def print_excel_report(self):
        """ Function is used to print the Excel report
            It will pass the invoice data through js file to
            print Excel file"""
        # Take the ids of the selected invoices
        data = self._context['active_ids']
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'account.move',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Invoice Excel Report', }, }

    def get_xlsx_report(self, datas, response):
        """ From this function we can create and design the Excel file template
         and the map the values in the corresponding cells
         :param datas: Selected record ids
         :param response: Response after creating excel
         """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # for printing multiple sheet per file, iterate the invoices
        for account_move in self.env['account.move'].browse(datas):
            # Set file title as invoice when it is invoice and set bill
            # if the move_type is out_invoice
            account_name = 'INVOICE - ' + account_move.name if \
                account_move.move_type == 'out_invoice' else \
                'VENDOR BILL - ' + account_move.name
            company_name = 'Company Name : ' + account_move.company_id.name
            # Copy the value to a variable set black if it is null
            # instead of printing 'FALSE' in the report
            ref = str(
                account_move.payment_reference) if \
                account_move.payment_reference is not False else ''
            # Copy the value to a variable set black if it is null
            # instead of printing 'FALSE' in the report
            payment_term = str(
                account_move.invoice_payment_term_id.name) if \
                account_move.invoice_payment_term_id.name is not False else ''
            # Copy the value to a variable set black if it is null instead
            # of printing 'FALSE' in the report
            fiscal_position = str(
                account_move.fiscal_position_id.name) if \
                account_move.fiscal_position_id.name is not False else ''
            # Copy the value to a variable set black if it is null
            # instead of printing 'FALSE' in the report
            sale_person = account_move.user_id.name if \
                account_move.user_id.name is not False else ''
            # Copy the value to a variable set black if it is null
            # instead of printing 'FALSE' in the report
            incoterm = account_move.invoice_incoterm_id.name if \
                account_move.invoice_incoterm_id.name is not False else ''
            invoice_date = str(account_move.invoice_date)
            currency_symbol = account_move.currency_id.symbol
            sheet = workbook.add_worksheet(
                account_move.name)  # Set sheet name as Invoice/Bill name
            sheet.set_column(0, 8, 20)
            head = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': '20px'})
            txt = workbook.add_format(
                {'align': 'center', 'bold': True})
            txt_border = workbook.add_format(
                {'align': 'center', 'bold': True, 'border': 1})
            border = workbook.add_format({'border': 1})
            sheet.merge_range('B2:E3', account_name, head)
            sheet.merge_range('B4:E4', company_name, txt)
            sheet.write('A6', 'Customer/Vendor Name', txt)
            sheet.write('B6', account_move.partner_id.name)
            sheet.write('B7', account_move.partner_id.street)
            sheet.write('B8', account_move.partner_id.state_id.name)
            sheet.write('B9', account_move.partner_id.zip)
            sheet.write('B10', account_move.partner_id.country_id.name)
            sheet.write('B11', account_move.partner_id.phone)
            sheet.write('D6', 'Date', txt)
            sheet.write('D7', 'Payment Term', txt)
            sheet.write('D8', 'Journal', txt)
            sheet.write('D9', 'Currency', txt)
            sheet.write('D10', 'State', txt)
            sheet.write('E6', invoice_date)
            sheet.write('E7', payment_term)
            sheet.write('E8', account_move.journal_id.name)
            sheet.write('E9', account_move.currency_id.name)
            sheet.write('E10', account_move.state)
            sheet.write('A13', 'Sales Persons', txt)
            sheet.write('A14', sale_person)
            sheet.write('B13', 'Source Document', txt)
            sheet.write('B14', ref)
            sheet.write('C13', 'Fiscal Position', txt)
            sheet.write('C14', fiscal_position)
            sheet.write('D13', 'Incoterm', txt)
            sheet.write('D14', incoterm)
            sheet.write('A16', 'Product', txt_border)
            sheet.write('B16', 'Description', txt_border)
            sheet.write('C16', 'Quantity', txt_border)
            sheet.write('D16', 'Account', txt_border)
            sheet.write('E16', 'Discount %', txt_border)
            sheet.write('F16', 'Unit Price', txt_border)
            sheet.write('G16', 'Tax', txt_border)
            sheet.write('H16', 'Subtotal', txt_border)
            row = 17
            self._add_invoice_line_to_excel(sheet, account_move, row, border, txt_border,
                               currency_symbol)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def _add_invoice_line_to_excel(self, sheet, account_move, row, border, txt_border,
                      currency_symbol):
        """
        Function to add invoice line values to the Excel file
        :param sheet: Current Excel sheet where data to be added
        :param account_move : Object of invoice in which data adding
        :param row:Excel row value of next data to be added
        :param border :Excel styling for adding border for each cell
        :param txt_border : Excel styling for adding data in each cell
        :param currency_symbol : Currency symbol of current record
        """
        for line in account_move.invoice_line_ids:
            # For adding value of the invoice lines
            tax = str(
                line.tax_ids.name) if line.tax_ids.name \
                                      is not False else ''
            sheet.write(row, 0, line.product_id.name, border)
            sheet.write(row, 1, line.name, border)
            sheet.write(row, 2, line.quantity, border)
            sheet.write(row, 3, line.account_id.display_name, border)
            sheet.write(row, 4, line.discount, border)
            sheet.write(row, 5, line.price_unit, border)
            sheet.write(row, 6, tax, border)
            sheet.write(row, 7,
                        str(currency_symbol) + str(line.price_subtotal),
                        border)
            row += 1
        row += 1
        sheet.write(row, 6, 'Total Amount', txt_border)
        sheet.write(row, 7,
                    str(currency_symbol) + str(account_move.amount_total),
                    border)
