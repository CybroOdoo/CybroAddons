# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

import json
import io
from xlsxwriter import workbook

from odoo.tools import date_utils
from odoo import fields, models
from odoo.exceptions import UserError, ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class SaleReportAdvance(models.TransientModel):
    _name = "sale.report.analysis"

    customer_ids = fields.Many2many('res.partner', string="Customers", required=True)
    product_ids = fields.Many2many('product.product', string='Products')
    from_date = fields.Date(string="Start Date")
    to_date = fields.Date(string="End Date")
    status = fields.Selection(
        [('all', 'All'), ('draft', 'Draft'), ('sent', 'Quotation Sent'), ('sale', 'Sale Order'), ('done', 'Locked')],
        string='Status', default='all', required=True)
    print_type = fields.Selection(
        [('sale', 'Sale Order'), ('product', 'Products')],
        string='Print By', default='sale', required=True)
    today_date = fields.Date(default=fields.Date.today())

    def get_analysis_report(self):
        datas = self._get_data()
        return self.env.ref('sale_report_advanced.action_sales_analysis').report_action([], data=datas)

    def _get_data(self):

        result = []
        if self.print_type == 'sale':
            if not self.status == 'all':
                sale_order = self.env['sale.order'].sudo().search([('state', '=', self.status),('state','!=','cancel')])
                filtered = self._get_filtered(sale_order)

            else:
                sale_order = self.env['sale.order'].search([('state','!=','cancel')])
                filtered = self._get_filtered(sale_order)

            for rec in filtered:
                paid = self._get_total_paid_amount(rec.invoice_ids)
                res = {
                    'so': rec.name,
                    'date': rec.date_order,
                    'sales_person': rec.user_id.name,
                    's_amt': rec.amount_total,
                    'p_amt': paid,
                    'balance': rec.amount_total - paid,
                    'partner_id': rec.partner_id,
                }
                result.append(res)
        else:
            if not self.status == 'all':
                sale_order_line = self.env['sale.order.line'].search([('order_id.state', '=', self.status),('order_id.state','!=','cancel')])
                filtered = self._get_filtered_order_line(sale_order_line)

            else:
                sale_order_line = self.env['sale.order.line'].search([('order_id.state','!=','cancel')])
                filtered = self._get_filtered_order_line(sale_order_line)

            for rec in filtered:
                res = {
                    'so': rec.order_id.name,
                    'date': rec.order_id.date_order,
                    'product_id': rec.product_id.name,
                    'price': rec.product_id.list_price,
                    'quantity': rec.product_uom_qty,
                    'discount': rec.discount,
                    'tax': rec.product_id.taxes_id.amount,
                    'total': rec.price_subtotal,
                    'partner_id': rec.order_id.partner_id,
                }
                result.append(res)
        datas = {
            'ids': self,
            'model': 'sale.report.analysis',
            'form': result,
            'partner_id': self._get_customers(),
            'start_date': self.from_date,
            'end_date': self.to_date,
            'type': self.print_type

        }
        return datas

    def _get_total_paid_amount(self, invoices):
        total = 0
        for inv in invoices:
            if inv.payment_state == 'paid':
                total += inv.amount_total
        return total

    def _get_filtered_order_line(self, sale_order_line):
        if self.from_date and self.to_date:
            filtered = list(filter(lambda
                                       x: x.order_id.date_order.date() >= self.from_date and x.order_id.date_order.date() <= self.to_date and x.order_id.partner_id in self.customer_ids and x.product_id in self.product_ids,
                                   sale_order_line))
        elif not self.from_date and self.to_date:
            filtered = list(filter(lambda
                                       x: x.order_id.date_order.date() <= self.to_date and x.order_id.partner_id in self.customer_ids and x.product_id in self.product_ids,
                                   sale_order_line))
        elif self.from_date and not self.to_date:
            filtered = list(filter(lambda
                                       x: x.order_id.date_order.date() >= self.from_date and x.order_id.partner_id in self.customer_ids and x.product_id in self.product_ids,
                                   sale_order_line))
        else:
            filtered = list(filter(lambda
                                       x: x.order_id.partner_id in self.customer_ids and x.product_id in self.product_ids,
                                   sale_order_line))
        return filtered

    def _get_filtered(self, sale_order):

        if self.from_date and self.to_date:
            filtered = list(filter(lambda
                                       x: x.date_order.date() >= self.from_date and x.date_order.date() <= self.to_date and x.partner_id in self.customer_ids,
                                   sale_order))
        elif not self.from_date and self.to_date:
            filtered = list(filter(lambda
                                       x: x.date_order.date() <= self.to_date and x.partner_id in self.customer_ids,
                                   sale_order))
        elif self.from_date and not self.to_date:
            filtered = list(filter(lambda
                                       x: x.date_order.date() >= self.from_date and x.partner_id in self.customer_ids,
                                   sale_order))
        else:
            filtered = list(filter(lambda
                                       x: x.partner_id in self.customer_ids,
                                   sale_order))
        return filtered

    def _get_customers(self):
        customers = []
        for rec in self.customer_ids:
            a = {
                'id': rec,
                'name': rec.name
            }
            customers.append(a)
        return customers

    def get_excel_analysis_report(self):
        datas = self._get_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'sale.report.analysis',
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

        if data['type'] == 'sale':
            sheet.merge_range('G2:L3', 'Sales Analysis Report', head)
            if data['start_date'] and data['end_date']:
                sheet.write('G6', 'From:', cell_format)
                sheet.merge_range('H6:I6', data['start_date'], txt)
                sheet.write('J6', 'To:', cell_format)
                sheet.merge_range('K6:L6', data['end_date'], txt)
            h_col = 9
        else:
            sheet.merge_range('G2:N3', 'Sales Analysis Report', head)
            if data['start_date'] and data['end_date']:
                sheet.write('G6', 'From:', cell_format)
                sheet.merge_range('H6:I6', data['start_date'], txt)
                sheet.write('K6', 'To:', cell_format)
                sheet.merge_range('L6:N6', data['end_date'], txt)
            h_col = 10

        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#f5f9ff', 'border': 1})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#6BA6FE', 'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'bg_color': '#95ff63', 'border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True})
        if data['partner_id']:
            record = data['partner_id']
        h_row = 7
        count = 0
        row = 5
        row_number = 6
        t_row = 6
        for rec in record:
            if data['type'] == 'sale':
                sheet.merge_range(h_row, h_col - 3, h_row, h_col + 2, rec['name'], format1)
                row = row + count + 3
                col = 6
                sheet.write(row, col, 'Order', format2)
                col += 1
                sheet.write(row, col, 'Date', format2)
                sheet.set_column('H:H', 17)
                col += 1
                sheet.write(row, col, 'Sales Person', format2)
                sheet.set_column('I:I', 15)
                col += 1
                sheet.write(row, col, 'Sales Amount', format2)
                sheet.set_column('J:J', 13)
                col += 1
                sheet.write(row, col, 'Amount Paid', format2)
                sheet.set_column('K:K', 12)
                col += 1
                sheet.write(row, col, 'Balance', format2)
                sheet.set_column('L:L', 10)
                # col = 6
                count = 0
                row_number = row_number + count + 3
                t_samt = 0
                t_pamt = 0
                t_bal = 0
                t_col = 8
                for val in data['form']:
                    if val['partner_id'] == rec['id']:
                        count += 1
                        column_number = 6
                        sheet.write(row_number, column_number, val['so'], format1)
                        column_number += 1
                        sheet.write(row_number, column_number, val['date'], format1)
                        sheet.set_column('H:H', 17)
                        column_number += 1
                        sheet.write(row_number, column_number, val['sales_person'], format1)
                        sheet.set_column('I:I', 15)
                        column_number += 1
                        sheet.write(row_number, column_number, val['s_amt'], format1)
                        sheet.set_column('J:J', 13)
                        t_samt += val['s_amt']
                        column_number += 1
                        sheet.write(row_number, column_number, val['p_amt'], format1)
                        sheet.set_column('K:K', 12)
                        t_pamt += val['p_amt']
                        column_number += 1
                        sheet.write(row_number, column_number, val['balance'], format1)
                        sheet.set_column('L:L', 10)
                        t_bal += val['balance']
                        column_number += 1
                        row_number += 1
                t_row = t_row + count + 3
                sheet.write(t_row, t_col, 'Total', format4)
                t_col += 1
                sheet.write(t_row, t_col, t_samt, format4)
                t_col += 1
                sheet.write(t_row, t_col, t_pamt, format4)
                t_col += 1
                sheet.write(t_row, t_col, t_bal, format4)
                h_row = h_row + count + 3

            if data['type'] == 'product':
                sheet.merge_range(h_row, h_col - 4, h_row, h_col + 3, rec['name'], format1)
                row = row + count + 3
                col = 6
                sheet.write(row, col, 'Order', format2)
                col += 1
                sheet.write(row, col, 'Date', format2)
                sheet.set_column('H:H', 17)
                col += 1
                sheet.write(row, col, 'Product', format2)
                sheet.set_column('I:I', 17)
                col += 1
                sheet.write(row, col, 'Quantity', format2)
                sheet.set_column('J:J', 7)
                col += 1
                sheet.write(row, col, 'Price', format2)
                sheet.set_column('K:K', 12)
                col += 1
                sheet.write(row, col, 'Discount(%)', format2)
                sheet.set_column('L:L', 12)
                col += 1
                sheet.write(row, col, 'Tax(%)', format2)
                sheet.set_column('M:M', 10)
                col += 1
                sheet.write(row, col, 'Subtotal', format2)
                sheet.set_column('N:N', 10)
                col += 1
                count = 0
                row_number = row_number + count + 3
                t_qty = 0
                t_price = 0
                t_tax = 0
                t_total = 0
                t_col = 8
                for val in data['form']:
                    if val['partner_id'] == rec['id']:
                        count += 1
                        column_number = 6
                        sheet.write(row_number, column_number, val['so'], format1)
                        column_number += 1
                        sheet.write(row_number, column_number, val['date'], format1)
                        sheet.set_column('H:H', 17)
                        column_number += 1
                        sheet.write(row_number, column_number, val['product_id'], format1)
                        sheet.set_column('I:I', 17)
                        column_number += 1
                        sheet.write(row_number, column_number, val['quantity'], format1)
                        sheet.set_column('J:J', 7)
                        t_qty += val['quantity']
                        column_number += 1
                        sheet.write(row_number, column_number, val['price'], format1)
                        sheet.set_column('K:K', 12)
                        t_price += val['price']
                        column_number += 1
                        sheet.write(row_number, column_number, val['discount'], format1)
                        sheet.set_column('L:L', 12)
                        column_number += 1
                        sheet.write(row_number, column_number, val['tax'], format1)
                        sheet.set_column('M:M', 10)
                        t_tax += val['tax']
                        column_number += 1
                        sheet.write(row_number, column_number, val['total'], format1)
                        sheet.set_column('N:N', 10)
                        t_total += val['total']
                        column_number += 1
                        row_number += 1
                t_row = t_row + count + 3
                sheet.write(t_row, t_col, 'Total', format4)
                t_col += 1
                sheet.write(t_row, t_col, t_qty, format4)
                t_col += 1
                sheet.write(t_row, t_col, t_price, format4)
                t_col += 2
                sheet.write(t_row, t_col, t_tax, format4)
                t_col += 1
                sheet.write(t_row, t_col, t_total, format4)
                h_row = h_row + count + 3
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
