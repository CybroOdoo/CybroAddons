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


class SaleOrder(models.Model):
    """ Added a function that to print sale order excel report
            which is added through server action """
    _inherit = "sale.order"

    def print_excel_report(self):
        """ Function is used to print the Excel report
                    It will pass the sale order data through js file to
                    print Excel file"""
        # Take the ids of the selected sale orders
        data = self._context['active_ids']
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'sale.order',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Sale/Quotation Excel Report', }, }

    def get_xlsx_report(self, datas, response):
        """ From this function we can create and design the Excel file template
                 and the map the values in the corresponding cells
            :param datas:Selected record ids
            :param response: Response after creating excel
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # for printing multiple sheet per file, iterate the sale orders
        for sale in self.env['sale.order'].browse(datas):
            sale_name = 'SALE ORDER - ' + sale.name
            company_name = 'Company Name : ' + sale.company_id.name
            # Copy the value to a variable set black if it is null
            # instead of printing 'FALSE' in the report
            ref = str(
                sale.client_order_ref) if \
                sale.client_order_ref is not False else ''
            # Copy the value to a variable set black if it is null instead
            # of printing 'FALSE' in the report
            payment_term = str(
                sale.payment_term_id.name) if \
                sale.payment_term_id.name is not False else ''
            # Copy the value to a variable set black if it is null instead
            # of printing 'FALSE' in the report
            fiscal_position = str(
                sale.fiscal_position_id.name) if \
                sale.fiscal_position_id.name is not False else ''
            sheet = workbook.add_worksheet(
                sale.name)  # set the sheet name as sale order name
            sheet.set_column(0, 8, 20)
            sale_date = str(sale.date_order)
            currency_symbol = sale.currency_id.symbol
            head = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': '20px'})
            txt = workbook.add_format({'align': 'center', 'bold': True})
            txt_border = workbook.add_format(
                {'align': 'center', 'bold': True, 'border': 1})
            border = workbook.add_format({'border': 1})
            sheet.merge_range('B2:E3', sale_name, head)
            sheet.merge_range('B4:E4', company_name, txt)
            sheet.write('A6', 'Customer Name', txt)
            sheet.write('B6', sale.partner_id.name)
            sheet.write('B7', sale.partner_id.street)
            sheet.write('B8', sale.partner_id.state_id.name)
            sheet.write('B9', sale.partner_id.zip)
            sheet.write('B10', sale.partner_id.country_id.name)
            sheet.write('B11', sale.partner_id.phone)
            sheet.write('D6', 'Date', txt)
            sheet.write('D7', 'Payment Term', txt)
            sheet.write('D8', 'Price List', txt)
            sheet.write('D9', 'State', txt)
            sheet.write('E6', sale_date)
            sheet.write('E7', payment_term)
            sheet.write('E8', sale.pricelist_id.name)
            sheet.write('E9', sale.state)
            sheet.write('A13', 'Sales Team', txt)
            sheet.write('A14', sale.team_id.name)
            sheet.write('B13', 'Sales Persons', txt)
            sheet.write('B14', sale.user_id.name)
            sheet.write('C13', 'Source Document', txt)
            sheet.write('C14', ref)
            sheet.write('D13', 'Fiscal Position', txt)
            sheet.write('D14', fiscal_position)
            sheet.write('A16', 'Product', txt_border)
            sheet.write('B16', 'Description', txt_border)
            sheet.write('C16', 'Quantity', txt_border)
            sheet.write('D16', 'Delivered', txt_border)
            sheet.write('E16', 'Invoiced', txt_border)
            sheet.write('F16', 'Unit Price', txt_border)
            sheet.write('G16', 'Tax', txt_border)
            sheet.write('H16', 'Subtotal', txt_border)
            row = 17
            # calling this function for adding sale order line data to the
            # Excel sheet
            self._add_order_line_to_excel(sheet, sale, row, border, txt_border,
                                          currency_symbol)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def _add_order_line_to_excel(self, sheet, sale, row, border, txt_border,
                                 currency_symbol):
        """
                Function to add sale order line values to the Excel file
                :param sheet: Current Excel sheet where data to be added
                :param sale : Object of sale order in which data adding
                :param row:Excel row value of next data to be added
                :param border :Excel styling for adding border for each cell
                :param txt_border : Excel styling for adding data in each cell
                :param currency_symbol : Currency symbol of current record
                """
        for line in sale.order_line:
            # For adding value of the sale order lines

            tax = str(
                line.tax_id.name) if line.tax_id.name is not False else ''
            sheet.write(row, 0, line.product_id.name, border)
            sheet.write(row, 1, line.name, border)
            sheet.write(row, 2, line.product_uom_qty, border)
            sheet.write(row, 3, line.qty_delivered, border)
            sheet.write(row, 4, line.qty_invoiced, border)
            sheet.write(row, 5, line.price_unit, border)
            sheet.write(row, 6, tax, border)
            sheet.write(row, 7,
                        str(currency_symbol) + str(line.price_subtotal),
                        border)
            row += 1
        row += 1
        sheet.write(row, 6, 'Total Amount', txt_border)
        sheet.write(row, 7, str(currency_symbol) + str(sale.amount_total),
                    border)
