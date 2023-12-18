# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Ayana KP (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import json
import io
from odoo.tools import date_utils
from odoo.exceptions import ValidationError
from odoo import fields, models
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class SaleReportAdvance(models.TransientModel):
    """ This transient model is used to create and configure parameters
    for generating reports related to sales."""
    _name = "sale.report.advance"
    _description = 'Sale Report Advance'

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
    today_date = fields.Date(string='Date', default=fields.Date.today(),
                             help="Default value is set to today's date"
                                  " for the report.")

    def _get_data(self):
        """ Function generating data for report in sale advance report """
        sales_order_line = self.env['sale.order.line'].search(
            [('order_id.state', '!=', 'cancel')])
        domain = [('state', '!=', 'cancel')]
        if self.from_date:
            domain.append(('date_order', '>=', self.from_date))
        if self.to_date:
            domain.append(('date_order', '<=', self.to_date))
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))
        sales_order = self.env['sale.order'].search(domain)
        if not sales_order:
            raise ValidationError("No data available for printing.")
        result = []
        customers = []
        products = []
        for rec in self.customer_ids:
            data = {
                'id': rec,
                'name': rec.name
            }
            customers.append(data)
        for rec in self.product_ids:
            data = {
                'id': rec,
                'name': rec.name
            }
            products.append(data)
        margin = 0
        if self.type == 'product':
            for rec in products:
                for lines in sales_order_line:
                    if lines.product_id == rec['id']:
                        profit = round(
                            lines.product_id.list_price - lines.product_id.standard_price,
                            2)
                        if lines.product_id.standard_price != 0:
                            margin = round((profit * 100) / lines.product_id.standard_price,2)
                        res = {
                            'sequence': lines.order_id.name,
                            'date': lines.order_id.date_order,
                            'product_id': lines.product_id,
                            'quantity': lines.product_uom_qty,
                            'cost': lines.product_id.standard_price,
                            'price': lines.product_id.list_price,
                            'profit': profit,
                            'margin': margin,
                            'partner': lines.order_id.partner_id.name,
                        }
                        result.append(res)
        if self.type == 'customer':
            for rec in customers:
                for so in sales_order:
                    if so.partner_id == rec['id']:
                        for lines in so.order_line:
                            profit = round(
                                lines.product_id.list_price - lines.product_id.standard_price,
                                2)
                            if lines.product_id.standard_price != 0:
                                margin = round((profit * 100) / lines.product_id.standard_price, 2)
                            res = {
                                'sequence': so.name,
                                'date': so.date_order,
                                'product': lines.product_id.name,
                                'quantity': lines.product_uom_qty,
                                'cost': lines.product_id.standard_price,
                                'price': lines.product_id.list_price,
                                'profit': profit,
                                'margin': margin,
                                'partner_id': so.partner_id,
                            }
                            result.append(res)
        if self.type == 'both':
            for rec in customers:
                for p in products:
                    for so in sales_order:
                        if so.partner_id == rec['id']:
                            for lines in so.order_line:
                                if lines.product_id == p['id']:
                                    profit = round(
                                        lines.product_id.list_price - lines.product_id.standard_price,
                                        2)
                                    if lines.product_id.standard_price != 0:
                                        margin = round((profit * 100) / lines.product_id.standard_price, 2)
                                    res = {
                                        'sequence': so.name,
                                        'date': so.date_order,
                                        'product': lines.product_id.name,
                                        'quantity': lines.product_uom_qty,
                                        'cost': lines.product_id.standard_price,
                                        'price': lines.product_id.list_price,
                                        'profit': profit,
                                        'margin': margin,
                                        'partner': so.partner_id.name,
                                    }
                                    result.append(res)
        if self.from_date and self.to_date and not self.customer_ids and not self.product_ids:
            for so in sales_order:
                for lines in so.order_line:
                    profit = round(
                        lines.product_id.list_price - lines.product_id.standard_price,
                        2)
                    if lines.product_id.standard_price != 0:
                        margin = round(
                            (profit * 100) / lines.product_id.standard_price, 2)
                    res = {
                        'sequence': so.name,
                        'date': so.date_order,
                        'product': lines.product_id.name,
                        'quantity': lines.product_uom_qty,
                        'cost': lines.product_id.standard_price,
                        'price': lines.product_id.list_price,
                        'profit': profit,
                        'margin': margin,
                        'partner': so.partner_id.name,
                    }
                    result.append(res)
        if not result:
            raise ValidationError("No data available for printing.")
        datas = {
            'ids': self,
            'model': 'sale.report.advance',
            'form': result,
            'partner_id': customers,
            'product_id': products,
            'start_date': self.from_date,
            'end_date': self.to_date,
            'type': self.type,
            'no_value': False,
        }
        if self.from_date and self.to_date and not self.customer_ids and not self.product_ids:
            datas['no_value'] = True
        return datas

    def action_get_report(self):
        """ Generate and display a custom sales report.
            :return: An action to display the custom sales report.
            :rtype: dict  """
        datas = self._get_data()
        return self.env.ref(
            'sale_report_advanced.action_sale_report').report_action([],
                                                                     data=datas)

    def action_get_excel_report(self):
        """ Generate and return an Excel report for advanced sales reporting.
            :return: A dictionary describing the action to be performed for
             the Excel report.
            :rtype: dict """
        datas = self._get_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'sale.report.advance',
                     'output_format': 'xlsx',
                     'options': json.dumps(datas,
                                           default=date_utils.json_default),
                     'report_name': 'Sale Advance Report',
                     },
        }

    def get_xlsx_report(self, data, response):
        """Function for generating xlsx report """
        loaded_data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        record = []
        cell_format = workbook.add_format({'font_size': '12px', })
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        sheet.merge_range('G2:N3', 'Sales Profit Report', head)
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
                t_margin = 0
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
                            t_margin += val['margin']
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
                            t_margin += val['margin']
                            column_number += 1
                            row_number += 1
                t_row = t_row + count + 3
                sheet.write(t_row, t_col, 'Total', format4)
                t_col += 1
                sheet.write(t_row, t_col, t_qty, format4)
                t_col += 1
                sheet.write(t_row, t_col, t_cost, format4)
                t_col += 1
                sheet.write(t_row, t_col, t_price, format4)
                t_col += 1
                sheet.write(t_row, t_col, t_profit, format4)
                t_col += 1
                sheet.write(t_row, t_col, t_margin, format4)
                t_col += 1
                h_row = h_row + count + 3
        if loaded_data.get('type') == 'both' or loaded_data.get(
                'no_value') == True:
            row += 3
            row_number += 2
            t_qty = 0
            t_cost = 0
            t_price = 0
            t_profit = 0
            t_margin = 0
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
                t_margin += val['margin']
                column_number += 1
                row_number += 1
            sheet.write(row_number, t_col, 'Total', format4)
            t_col += 1
            sheet.write(row_number, t_col, t_qty, format4)
            t_col += 1
            sheet.write(row_number, t_col, t_cost, format4)
            t_col += 1
            sheet.write(row_number, t_col, t_price, format4)
            t_col += 1
            sheet.write(row_number, t_col, t_profit, format4)
            t_col += 1
            sheet.write(row_number, t_col, t_margin, format4)
            t_col += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
