# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import io
import json
from odoo import fields, models
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class SaleReportCategory(models.TransientModel):
    """This class is to add sale.report.category."""

    _name = "sale.report.category"
    _description = "Sale Category Report"

    category_ids = fields.Many2many(
        'product.category', string="Categories", help="Product Categories",
        required=True)
    from_date = fields.Date(string="Start Date", help="Start Date")
    to_date = fields.Date(string="End Date", help="End Date")
    company_ids = fields.Many2many(
        'res.company', string='Companies', help='Companies')
    today_date = fields.Date(default=fields.Date.today(), string='Today',
                             help='Today')

    def action_get_category_report(self):
        """produces a report on sales category and returns it as an action."""
        datas = self._get_data()
        return self.env.ref(
            'all_in_one_sales_kit.sale_category_action').report_action(
            [], data=datas)

    def _get_data(self):
        """ Retrieves information based on the filter parameters selected
                 on the current instance."""
        sale_order_line = self.env['sale.order.line'].search(
            [('order_id.state', '!=', 'cancel')])
        if self.from_date and self.to_date and self.company_ids:
            order_lines = list(filter(
                lambda x: self.from_date >= x.order_id.date_order.date(
                ) <= self.to_date and x.order_id.company_id in
                          self.company_ids, sale_order_line))
            category = self._get_category()
            res = self._get_category_wise(order_lines, category)
        elif not self.from_date and self.to_date and self.company_ids:
            order_lines = list(filter(
                lambda x: x.order_id.date_order.date() <= self.to_date and
                          x.order_id.company_id in self.company_ids,
                sale_order_line))
            category = self._get_category()
            res = self._get_category_wise(order_lines, category)
        elif self.from_date and not self.to_date and self.company_ids:
            order_lines = list(filter(
                lambda x: self.from_date >= x.order_id.date_order.date() and
                          x.order_id.company_id in self.company_ids,
                sale_order_line))
            category = self._get_category()
            res = self._get_category_wise(order_lines, category)
        elif self.from_date and self.to_date and not self.company_ids:
            order_lines = list(filter(
                lambda x: self.from_date >= x.order_id.date_order.date(
                ) <= self.to_date, sale_order_line))
            category = self._get_category()
            res = self._get_category_wise(order_lines, category)
        elif not self.from_date and not self.to_date and self.company_ids:
            order_lines = list(filter(
                lambda x: x.order_id.company_id in self.company_ids,
                sale_order_line))
            category = self._get_category()
            res = self._get_category_wise(order_lines, category)
        elif not self.from_date and self.to_date and not self.company_ids:
            order_lines = list(filter(
                lambda x: x.order_id.date_order.date() <= self.to_date,
                sale_order_line))
            category = self._get_category()
            res = self._get_category_wise(order_lines, category)
        elif self.from_date and not self.to_date and not self.company_ids:
            order_lines = list(filter(
                lambda x: self.from_date >= x.order_id.date_order.date(),
                sale_order_line))
            category = self._get_category()
            res = self._get_category_wise(order_lines, category)
        else:
            category = self._get_category()
            res = self._get_category_wise(sale_order_line, category)
        datas = {
            'ids': self,
            'model': 'sale.report.category',
            'form': res,
            'categ_id': category,
            'start_date': self.from_date,
            'end_date': self.to_date,
        }
        return datas

    def _get_category_wise(self, order_lines, category):
        """Returns the sales data grouped by category."""
        result = []
        for cat in category:
            for lines in order_lines:
                if cat['id'] == lines.product_id.categ_id:
                    total = lines.product_id.taxes_id.amount + \
                            lines.price_subtotal
                    res = {
                        'so': lines.order_id.name,
                        'date': lines.order_id.date_order,
                        'product_id': lines.product_id.name,
                        'quantity': lines.product_uom_qty,
                        'tax': lines.product_id.taxes_id.amount,
                        'uom': lines.product_id.uom_id.name,
                        'price': lines.product_id.list_price,
                        'subtotal': lines.price_subtotal,
                        'total': total,
                        'category_id': lines.product_id.categ_id,
                    }
                    result.append(res)
        return result

    def _get_category(self):
        """Retrieve the category information for the selected category_ids."""
        category = []
        for rec in self.category_ids:
            a = {
                'id': rec,
                'name': rec.complete_name
            }
            category.append(a)
        return category

    def action_get_excel_category_report(self):
        """This function retrieves sale order line data based on the current
         filters set in the wizard, and generates a list of dictionaries with
          sale order line details grouped by product category."""
        datas = self._get_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'sale.report.category',
                     'output_format': 'xlsx',
                     'options': json.dumps(
                         datas, default=date_utils.json_default),
                     'report_name': 'Excel Report Name',
                     },
        }

    def get_xlsx_report(self, data, response):
        """To pass data to the xlsx report."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        record = []
        cell_format = workbook.add_format({'font_size': '12px', })
        head = workbook.add_format({'align': 'center',
                                    'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        sheet.merge_range('G2:O3', 'Sales Category Report', head)
        if data['start_date'] and data['end_date']:
            sheet.write('G6', 'From:', cell_format)
            sheet.merge_range('H6:I6', data['start_date'], txt)
            sheet.write('M6', 'To:', cell_format)
            sheet.merge_range('N6:O6', data['end_date'], txt)
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center',
             'bg_color': '#bbd5fc', 'border': 1})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#6BA6FE', 'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center',
             'bold': True, 'border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center',
             'bold': True, 'bg_color': '#c0dbfa'})
        h_row = 7
        h_col = 10
        count = 0
        row = 5
        col = 6
        row_number = 6
        t_row = 6
        if data['categ_id']:
            record = data['categ_id']
            for rec in record:
                sheet.merge_range(
                    h_row, h_col - 4, h_row, h_col + 4, rec['name'], format4)
                row = row + count + 3
                sheet.write(row, col, 'Order', format2)
                col += 1
                sheet.write(row, col, 'Date', format2)
                sheet.set_column('H:H', 15)
                col += 1
                sheet.write(row, col, 'Product', format2)
                sheet.set_column('I:I', 20)
                col += 1
                sheet.write(row, col, 'UOM', format2)
                col += 1
                sheet.write(row, col, 'Quantity', format2)
                col += 1
                sheet.write(row, col, 'Price', format2)
                col += 1
                sheet.write(row, col, 'Tax(%)', format2)
                col += 1
                sheet.write(row, col, 'Subtotal', format2)
                col += 1
                sheet.write(row, col, 'Total', format2)
                col += 1
                col = 6
                count = 0
                row_number = row_number + count + 3
                t_qty = 0
                t_price = 0
                t_subtotal = 0
                t_total = 0
                t_col = 9
                for val in data['form']:
                    if val['category_id'] == rec['id']:
                        count += 1
                        column_number = 6
                        sheet.write(
                            row_number, column_number,
                            val['so'], format1)
                        column_number += 1
                        sheet.write(
                            row_number, column_number,
                            val['date'], format1)
                        sheet.set_column('H:H', 15)
                        column_number += 1
                        sheet.write(
                            row_number, column_number,
                            val['product_id'], format1)
                        sheet.set_column('I:I', 20)
                        column_number += 1
                        sheet.write(
                            row_number, column_number,
                            val['uom'], format1)
                        column_number += 1
                        sheet.write(
                            row_number, column_number,
                            val['quantity'], format1)
                        t_qty += val['quantity']
                        column_number += 1
                        sheet.write(
                            row_number, column_number,
                            val['price'], format1)
                        t_price += val['price']
                        column_number += 1
                        sheet.write(
                            row_number, column_number,
                            val['tax'], format1)
                        column_number += 1
                        sheet.write(
                            row_number, column_number,
                            val['subtotal'], format1)
                        t_subtotal += val['subtotal']
                        column_number += 1
                        sheet.write(
                            row_number, column_number,
                            val['total'], format1)
                        t_total += val['total']
                        column_number += 1
                        row_number += 1
                t_row = t_row + count + 3
                sheet.write(t_row, t_col, 'Total', format3)
                t_col += 1
                sheet.write(t_row, t_col, t_qty, format3)
                t_col += 1
                sheet.write(t_row, t_col, t_price, format3)
                t_col += 2
                sheet.write(t_row, t_col, t_subtotal, format3)
                t_col += 1
                sheet.write(t_row, t_col, t_total, format3)
                t_col += 1
                h_row = h_row + count + 3
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
