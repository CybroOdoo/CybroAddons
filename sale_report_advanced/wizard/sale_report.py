# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import json
import io
from datetime import datetime
from xlsxwriter import workbook

from odoo.tools import date_utils
from odoo import fields, models
from odoo.exceptions import UserError, ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class SaleReportAdvance(models.TransientModel):
    _name = "sale.report.advance"

    customer_ids = fields.Many2many('res.partner', string="Customers")
    product_ids = fields.Many2many('product.product', string='Products')
    from_date = fields.Date(string="Start Date")
    to_date = fields.Date(string="End Date")
    type = fields.Selection([('customer', 'Customers'), ('product', 'Products'), ('both', 'Both')],
                            string='Report Print By', default='customer', reqired=True)
    company_ids = fields.Many2many('res.company', string='Companies')
    today_date = fields.Date(default=fields.Date.today())

    def _get_data(self):
        sale = self.env['sale.order'].search([('state','!=','cancel')])
        sales_order_line = self.env['sale.order.line'].search([('order_id.state','!=','cancel')])

        if self.from_date and self.to_date and self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.date_order.date() >= self.from_date and x.date_order.date() <= self.to_date and x.company_id in self.company_ids,
                                      sale))
        elif not self.from_date and self.to_date and self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.date_order.date() <= self.to_date and x.company_id in self.company_ids,
                                      sale))
        elif self.from_date and not self.to_date and self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.date_order.date() >= self.from_date and x.company_id in self.company_ids,
                                      sale))
        elif self.from_date and self.to_date and not self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.date_order.date() >= self.from_date and x.date_order.date() <= self.to_date,
                                      sale))
        elif not self.from_date and not self.to_date and self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.company_id in self.company_ids,
                                      sale))
        elif not self.from_date and self.to_date and not self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.date_order.date() <= self.to_date,
                                      sale))
        elif self.from_date and not self.to_date and not self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.date_order.date() >= self.from_date,
                                      sale))
        else:
            sales_order = sale
        result = []
        customers = []
        products = []
        for rec in self.customer_ids:
            a = {
                'id': rec,
                'name': rec.name
            }
            customers.append(a)
        for rec in self.product_ids:
            a = {
                'id': rec,
                'name': rec.name
            }
            products.append(a)

        if self.type == 'product':
            for rec in products:
                for lines in sales_order_line:
                    if lines.product_id == rec['id']:
                        profit = round(lines.product_id.list_price - lines.product_id.standard_price, 2)
                        if lines.product_id.standard_price != 0:
                            margin = round((profit * 100) / lines.product_id.standard_price, 2)
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
                            profit = round(lines.product_id.list_price - lines.product_id.standard_price, 2)
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
                                    profit = round(lines.product_id.list_price - lines.product_id.standard_price, 2)
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
                    profit = round(lines.product_id.list_price - lines.product_id.standard_price, 2)
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
            datas['no_value']=True
        return datas

    def get_report(self):
        datas = self._get_data()
        return self.env.ref('sale_report_advanced.action_sale_report').report_action([], data=datas)

    def get_excel_report(self):
        datas = self._get_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'sale.report.advance',
                     'output_format': 'xlsx',
                     'options': json.dumps(datas, default=date_utils.json_default),
                     'report_name': 'Excel Report Name',
                     },
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        record = []
        cell_format = workbook.add_format({'font_size': '12px', })
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        sheet.merge_range('G2:N3', 'Sales Profit Report', head)
        if data['start_date'] and data['end_date']:
            sheet.write('G6', 'From:', cell_format)
            sheet.merge_range('H6:I6', data['start_date'], txt)
            sheet.write('L6', 'To:', cell_format)
            sheet.merge_range('M6:N6', data['end_date'], txt)
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center','bg_color':'#bbd5fc','border': 1})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#6BA6FE', 'border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'bg_color': '#c0dbfa', 'border': 1})
        if data['type'] == 'product':
            record = data['product_id']
        if data['type'] == 'customer':
            record = data['partner_id']
        h_row = 7
        h_col = 9
        count = 0
        row = 5
        col = 6
        row_number = 6
        t_row = 6
        if data['type'] == 'product' or data['type'] == 'customer':
            for rec in record:
                sheet.merge_range(h_row, h_col-3,h_row,h_col+4,rec['name'], format3)
                row = row + count + 3
                sheet.write(row, col, 'Order', format2)
                col += 1
                sheet.write(row, col, 'Date', format2)
                sheet.set_column('H:H', 15)
                col += 1
                if data['type'] == 'product':
                    sheet.write(row, col, 'Customer', format2)
                    sheet.set_column('I:I', 20)
                    col += 1
                elif data['type'] == 'customer':
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
                for val in data['form']:
                    if data['type'] == 'customer':
                        if val['partner_id'] == rec['id']:
                            count += 1
                            column_number = 6
                            sheet.write(row_number, column_number, val['sequence'], format1)
                            column_number += 1
                            sheet.write(row_number, column_number, val['date'], format1)
                            sheet.set_column('H:H', 15)
                            column_number += 1
                            sheet.write(row_number, column_number, val['product'], format1)
                            sheet.set_column('I:I', 20)
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
                    if data['type'] == 'product':
                        if val['product_id'] == rec['id']:
                            count += 1
                            column_number = 6
                            sheet.write(row_number, column_number, val['sequence'], format1)
                            column_number += 1
                            sheet.write(row_number, column_number, val['date'], format1)
                            sheet.set_column('H:H', 15)
                            column_number += 1
                            sheet.write(row_number, column_number, val['partner'], format1)
                            sheet.set_column('I:I', 20)
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
        if data['type'] == 'both' or data['no_value'] == True:
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
            row_number+=1
            for val in data['form']:
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
