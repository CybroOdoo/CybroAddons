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
    _name = "sale.report.indent"

    customer_ids = fields.Many2many('res.partner', string="Customers", required=True)
    category_ids = fields.Many2many('product.category', string="Categories", required=True)
    from_date = fields.Date(string="Start Date")
    to_date = fields.Date(string="End Date")
    status = fields.Selection(
        [('all', 'All'), ('draft', 'Draft'), ('sent', 'Quotation Sent'), ('sale', 'Sale Order'), ('done', 'Locked')],
        string='Status', default='all', required=True)
    company_ids = fields.Many2many('res.company', string='Companies')
    today_date = fields.Date(default=fields.Date.today())

    def get_category_report(self):
        datas = self._get_data()
        return self.env.ref('sale_report_advanced.action_sale_indent').report_action([], data=datas)

    def _get_data(self):

        sale_order_line = self.env['sale.order.line'].search([('order_id.state','!=','cancel')])
        if self.from_date and self.to_date and self.company_ids:
            order_lines = list(filter(lambda
                                          x: x.order_id.date_order.date() >= self.from_date and x.order_id.date_order.date() <= self.to_date and x.order_id.company_id in self.company_ids,
                                      sale_order_line))
            res = self._get_orders(order_lines)

        elif not self.from_date and self.to_date and self.company_ids:
            order_lines = list(filter(lambda
                                          x: x.order_id.date_order.date() <= self.to_date and x.order_id.company_id in self.company_ids,
                                      sale_order_line))
            res = self._get_orders(order_lines)
        elif self.from_date and not self.to_date and self.company_ids:
            order_lines = list(filter(lambda
                                          x:  x.order_id.date_order.date() >= self.from_date and x.order_id.company_id in self.company_ids,
                                      sale_order_line))
            res = self._get_orders(order_lines)
        elif self.from_date and self.to_date and not self.company_ids:
            order_lines = list(filter(lambda
                                          x:  x.order_id.date_order.date() >= self.from_date and x.order_id.date_order.date()<= self.to_date,
                                      sale_order_line))
            res = self._get_orders(order_lines)

        elif not self.from_date and not self.to_date and self.company_ids:
            order_lines = list(filter(lambda
                                          x: x.order_id.company_id in self.company_ids,
                                      sale_order_line))
            res = self._get_orders(order_lines)
        elif not self.from_date and self.to_date and not self.company_ids:
            order_lines = list(filter(lambda
                                          x: x.order_id.date_order.date() <= self.to_date,
                                      sale_order_line))
            res = self._get_orders(order_lines)
        elif self.from_date and not self.to_date and not self.company_ids:
            order_lines = list(filter(lambda
                                          x: x.order_id.date_order.date() >= self.from_date,
                                      sale_order_line))
            res = self._get_orders(order_lines)
        else:
            res = self._get_orders(sale_order_line)

        datas = {
            'ids': self,
            'model': 'sale.report.indent',
            'form': res,
            'categ_id': self._get_category(),
            'partner_id': self._get_customers(),
            'start_date': self.from_date,
            'end_date': self.to_date,

        }
        return datas

    def _get_orders(self, sale_order_line):
        if self.status == 'all':

            filtered_order = list(filter(lambda
                                             x: x.order_id.partner_id in self.customer_ids and x.product_id.categ_id in self.category_ids,
                                         sale_order_line))
        else:
            filtered_order = list(filter(lambda
                                             x: x.order_id.partner_id in self.customer_ids and x.order_id.state in self.status and x.product_id.categ_id in self.category_ids,
                                         sale_order_line))
        return self._get_customer_wise(filtered_order)

    def _get_customer_wise(self, order):
        result = []
        for rec in order:
            res = {
                'product_id': rec.product_id.name,
                'quantity': rec.product_uom_qty,
                'partner_id': rec.order_id.partner_id,
                'category_id': rec.product_id.categ_id,
            }
            result.append(res)
        return result

    def _get_category(self):
        category = []
        for rec in self.category_ids:
            a = {
                'id': rec,
                'name': rec.complete_name
            }
            category.append(a)
        return category

    def _get_customers(self):
        customers = []
        for rec in self.customer_ids:
            a = {
                'id': rec,
                'name': rec.name
            }
            customers.append(a)
        return customers

    def get_excel_category_report(self):
        datas = self._get_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'sale.report.indent',
                     'output_format': 'xlsx',
                     'options': json.dumps(datas, default=date_utils.json_default),
                     'report_name': 'Excel Report Name',
                     },
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px', })
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        sheet.merge_range('G2:N3', 'Product Sales Indent Report', head)
        if data['start_date'] and data['end_date']:
            sheet.write('G6', 'From:', cell_format)
            sheet.merge_range('H6:I6', data['start_date'], txt)
            sheet.write('L6', 'To:', cell_format)
            sheet.merge_range('M6:N6', data['end_date'], txt)
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#f5f9ff', 'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'bg_color': '#6BA6FE', 'border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'bg_color': '#b6d0fa', 'border': 1})
        if data['categ_id']:
            categ = data['categ_id']
        if data['partner_id']:
            partner = data['partner_id']
        h_row = 6
        h_col = 10
        c_row = 6
        row = 7
        row_number = 6
        for rec in partner:
            count = 0
            h_row += 1
            sheet.merge_range(h_row, h_col - 1, h_row, h_col, rec['name'], format3)
            c_row = c_row + 2
            row += 2
            row_number += 2
            for cat in categ:
                count += 2
                c_col = 10
                col = 9
                sheet.merge_range(c_row, c_col - 1, c_row, c_col, cat['name'], format1)
                sheet.write(row, col, 'Product', format4)
                sheet.set_column('J:J', 17)
                col += 1
                sheet.write(row, col, 'Quantity', format4)
                sheet.set_column('K:K', 17)
                row_number += 2
                c_count = 0
                for val in data['form']:
                    if val['category_id'] == cat['id'] and val['partner_id'] == rec['id']:
                        c_count += 1
                        count += 1
                        column_number = 9
                        sheet.write(row_number, column_number, val['product_id'], format1)
                        sheet.set_column('J:J', 17)
                        column_number += 1
                        sheet.write(row_number, column_number, val['quantity'], format1)
                        sheet.set_column('K:K', 17)
                        row_number += 1

                row = row + c_count + 2
                c_row = c_row + c_count + 2
            h_row = h_row + count + 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
