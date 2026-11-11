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

from odoo import fields, models


class SaleReportAdvance(models.TransientModel):
    """ This transient model is used to create and configure parameters
    for generating reports related to sales."""
    _name = "sale.report.advance"
    _inherit = 'sale.report.mixin'
    _description = 'Product Profit Report'

    customer_ids = fields.Many2many('res.partner',
                                    string="Customers", help="Select specific"
                                    " customers for the report.")
    product_ids = fields.Many2many('product.product',
                                   string='Products', help="Select specific"
                                   " products for the report.")
    from_date = fields.Date(string="Start Date", help="Specify the start date "
                                                      "of the report period.")
    to_date = fields.Date(string="End Date", help="Specify the end date of the "
                                                  "report period.")
    type = fields.Selection(
        [('customer', 'Customers'), ('product', 'Products'), ('both', 'Both')],
        string='Report Print By', default='customer', required=True,
        help="Choose the type of report to generate: by Customers, "
             "Products, or Both.")
    company_ids = fields.Many2many('res.company', string='Companies',
                                   help="Filter the report by "
                                        "selecting specific companies.")
    today_date = fields.Date(string='Date', default=fields.Date.context_today,
                             help="Default value is set to today's date"
                                  " for the report.")

    @staticmethod
    def _total_margin(cost, profit):
        """Return the margin of a total, the same way as for a line."""
        return round(profit * 100 / cost, 2) if cost else 0

    def _prepare_line(self, line):
        """Return the report values of a sale order line."""
        product = line.product_id
        cost = product.standard_price
        profit = round(product.list_price - cost, 2)
        order = line.order_id
        return {
            'sequence': order.name,
            'date': order.date_order,
            'product': product.name,
            'product_id': product,
            'quantity': line.product_uom_qty,
            'cost': cost,
            'price': product.list_price,
            'profit': profit,
            'margin': round(profit * 100 / cost, 2) if cost else 0,
            'partner': order.partner_id.name,
            'partner_id': order.partner_id,
        }

    def _get_data(self):
        """ Function generating data for report in sale advance report """
        domain = [
            ('order_id.state', '!=', 'cancel'),
            ('display_type', '=', False),
            *self._get_date_domain('order_id.date_order'),
        ]
        if self.company_ids:
            domain.append(('order_id.company_id', 'in', self.company_ids.ids))
        lines = self.env['sale.order.line'].search(domain)
        if not lines:
            self._raise_no_data()
        customers = [{'id': rec, 'name': rec.name}
                     for rec in self.customer_ids]
        products = [{'id': rec, 'name': rec.name}
                    for rec in self.product_ids]
        date_only = bool(self.from_date and self.to_date
                         and not self.customer_ids and not self.product_ids)
        if not date_only:
            if self.type != 'customer':
                lines = lines.filtered(
                    lambda line: line.product_id in self.product_ids)
            if self.type != 'product':
                lines = lines.filtered(
                    lambda line: line.order_id.partner_id in self.customer_ids)
        result = [self._prepare_line(line) for line in lines]
        if not result:
            self._raise_no_data()
        return {
            'ids': self.ids,
            'model': 'sale.report.advance',
            'form': result,
            'partner_id': customers,
            'product_id': products,
            'start_date': self.from_date,
            'end_date': self.to_date,
            'type': self.type,
            'no_value': date_only,
        }

    def action_get_report(self):
        """ Generate and display a custom sales report.
            :return: An action to display the custom sales report.
            :rtype: dict  """
        datas = self._get_data()
        return self._get_report_action(
            'sale_report_advanced.action_sale_report', datas)

    def action_get_excel_report(self):
        """ Generate and return an Excel report for advanced sales reporting.
            :return: A dictionary describing the action to be performed for
             the Excel report.
            :rtype: dict """
        datas = self._get_data()
        return self._get_xlsx_action(
            datas, self.env._('Product Profit Report'))

    def get_xlsx_report(self, data, response):
        """Function for generating xlsx report """
        loaded_data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        record = []
        cell_format = workbook.add_format({'font_size': 12})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': 20})
        txt = workbook.add_format({'font_size': 10, 'align': 'center'})
        sheet.merge_range('G2:N3', 'Product Profit Report', head)
        if loaded_data.get('start_date') and loaded_data.get('end_date'):
            sheet.write('G6', 'From:', cell_format)
            sheet.merge_range('H6:I6', loaded_data.get('start_date'), txt)
            sheet.write('L6', 'To:', cell_format)
            sheet.merge_range('M6:N6', loaded_data.get('end_date'), txt)
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#bbd5fc',
             'border': 1})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#6BA6FE', 'border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#c0dbfa', 'border': 1})
        if loaded_data.get('type') == 'product':
            record = loaded_data.get('product_id')
        if loaded_data.get('type') == 'customer':
            record = loaded_data.get('partner_id')
        h_row = 7
        h_col = 9
        count = 0
        row = 5
        col = 6
        row_number = 6
        t_row = 6
        if loaded_data.get('type') == 'product' or loaded_data.get(
                'type') == 'customer':
            for rec in record:
                sheet.merge_range(h_row, h_col - 3, h_row, h_col + 4,
                                  rec['name'], format3)
                row = row + count + 3
                sheet.write(row, col, 'Order', format2)
                col += 1
                sheet.write(row, col, 'Date', format2)
                sheet.set_column('H:H', 15)
                col += 1
                if loaded_data.get('type') == 'product':
                    sheet.write(row, col, 'Customer', format2)
                    sheet.set_column('I:I', 20)
                    col += 1
                elif loaded_data.get('type') == 'customer':
                    sheet.write(row, col, 'Product', format2)
                    sheet.set_column('I:I', 20)
                    col += 1
                sheet.write(row, col, 'Quantity', format2)
                col += 1
                sheet.write(row, col, 'Cost', format2)
                col += 1
                sheet.write(row, col, 'Price', format2)
                col += 1
                sheet.write(row, col, 'Profit', format2)
                col += 1
                sheet.write(row, col, 'Margin(%)', format2)
                col += 1
                col = 6
                count = 0
                row_number = row_number + count + 3
                t_qty = 0
                t_cost = 0
                t_price = 0
                t_profit = 0
                t_col = 8
                for val in loaded_data.get('form'):
                    if loaded_data.get('type') == 'customer':
                        if val['partner_id'] == rec['id']:
                            count += 1
                            column_number = 6
                            sheet.write(row_number, column_number,
                                        val['sequence'], format1)
                            column_number += 1
                            sheet.write(row_number, column_number, val['date'],
                                        format1)
                            sheet.set_column('H:H', 15)
                            column_number += 1
                            sheet.write(row_number, column_number,
                                        val['product'], format1)
                            sheet.set_column('I:I', 20)
                            column_number += 1
                            sheet.write(row_number, column_number,
                                        val['quantity'], format1)
                            t_qty += val['quantity']
                            column_number += 1
                            sheet.write(row_number, column_number, val['cost'],
                                        format1)
                            t_cost += val['cost']
                            column_number += 1
                            sheet.write(row_number, column_number, val['price'],
                                        format1)
                            t_price += val['price']
                            column_number += 1
                            sheet.write(row_number, column_number,
                                        val['profit'], format1)
                            t_profit += val['profit']
                            column_number += 1
                            sheet.write(row_number, column_number,
                                        val['margin'], format1)
                            column_number += 1
                            row_number += 1
                    if loaded_data.get('type') == 'product':
                        if val['product_id'] == rec['id']:
                            count += 1
                            column_number = 6
                            sheet.write(row_number, column_number,
                                        val['sequence'], format1)
                            column_number += 1
                            sheet.write(row_number, column_number, val['date'],
                                        format1)
                            sheet.set_column('H:H', 15)
                            column_number += 1
                            sheet.write(row_number, column_number,
                                        val['partner'], format1)
                            sheet.set_column('I:I', 20)
                            column_number += 1
                            sheet.write(row_number, column_number,
                                        val['quantity'], format1)
                            t_qty += val['quantity']
                            column_number += 1
                            sheet.write(row_number, column_number, val['cost'],
                                        format1)
                            t_cost += val['cost']
                            column_number += 1
                            sheet.write(row_number, column_number, val['price'],
                                        format1)
                            t_price += val['price']
                            column_number += 1
                            sheet.write(row_number, column_number,
                                        val['profit'], format1)
                            t_profit += val['profit']
                            column_number += 1
                            sheet.write(row_number, column_number,
                                        val['margin'], format1)
                            column_number += 1
                            row_number += 1
                t_row = t_row + count + 3
                sheet.write(t_row, t_col, 'Total', format4)
                t_col += 1
                sheet.write(t_row, t_col, t_qty, format4)
                t_col += 1
                sheet.write(t_row, t_col, round(t_cost, 2), format4)
                t_col += 1
                sheet.write(t_row, t_col, round(t_price, 2), format4)
                t_col += 1
                sheet.write(t_row, t_col, round(t_profit, 2), format4)
                t_col += 1
                sheet.write(t_row, t_col,
                            self._total_margin(t_cost, t_profit), format4)
                t_col += 1
                h_row = h_row + count + 3
        if loaded_data.get('type') == 'both' or loaded_data.get(
                'no_value'):
            row += 3
            row_number += 2
            t_qty = 0
            t_cost = 0
            t_price = 0
            t_profit = 0
            t_col = 9
            sheet.write(row, col, 'Order', format2)
            col += 1
            sheet.write(row, col, 'Date', format2)
            sheet.set_column('H:H', 15)
            col += 1
            sheet.write(row, col, 'Customer', format2)
            sheet.set_column('I:I', 20)
            col += 1
            sheet.write(row, col, 'Product', format2)
            sheet.set_column('J:J', 20)
            col += 1
            sheet.write(row, col, 'Quantity', format2)
            col += 1
            sheet.write(row, col, 'Cost', format2)
            col += 1
            sheet.write(row, col, 'Price', format2)
            col += 1
            sheet.write(row, col, 'Profit', format2)
            col += 1
            sheet.write(row, col, 'Margin', format2)
            col += 1
            row_number += 1
            for val in loaded_data.get('form'):
                column_number = 6
                sheet.write(row_number, column_number, val['sequence'], format1)
                column_number += 1
                sheet.write(row_number, column_number, val['date'], format1)
                sheet.set_column('H:H', 15)
                column_number += 1
                sheet.write(row_number, column_number, val['partner'], format1)
                sheet.set_column('I:I', 20)
                column_number += 1
                sheet.write(row_number, column_number, val['product'], format1)
                sheet.set_column('J:J', 20)
                column_number += 1
                sheet.write(row_number, column_number, val['quantity'], format1)
                t_qty += val['quantity']
                column_number += 1
                sheet.write(row_number, column_number, val['cost'], format1)
                t_cost += val['cost']
                column_number += 1
                sheet.write(row_number, column_number, val['price'], format1)
                t_price += val['price']
                column_number += 1
                sheet.write(row_number, column_number, val['profit'], format1)
                t_profit += val['profit']
                column_number += 1
                sheet.write(row_number, column_number, val['margin'], format1)
                column_number += 1
                row_number += 1
            sheet.write(row_number, t_col, 'Total', format4)
            t_col += 1
            sheet.write(row_number, t_col, t_qty, format4)
            t_col += 1
            sheet.write(row_number, t_col, round(t_cost, 2), format4)
            t_col += 1
            sheet.write(row_number, t_col, round(t_price, 2), format4)
            t_col += 1
            sheet.write(row_number, t_col, round(t_profit, 2), format4)
            t_col += 1
            sheet.write(row_number, t_col,
                        self._total_margin(t_cost, t_profit), format4)
            t_col += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
