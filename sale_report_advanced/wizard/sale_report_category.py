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

from odoo import api, fields, models


class SaleReportCategory(models.TransientModel):
    """ Model for handling sales report categories.  """
    _name = "sale.report.category"
    _inherit = 'sale.report.mixin'
    _description = 'Sales Category Report'

    category_ids = fields.Many2many('product.category',
                                    string="Categories", required=True,
                                    help="Select one or more product categories.")
    from_date = fields.Date(string="Start Date",
                            help="Specify the beginning date for your report.")
    to_date = fields.Date(string="End Date",
                          help="Specify the ending date for your report.")
    company_ids = fields.Many2many('res.company', string='Companies',
                                   help="Select one or more companies for the report.")
    today_date = fields.Date(string="Date", default=fields.Date.context_today,
                             help="Automatically set to the current date.")

    @api.constrains('from_date', 'to_date')
    def _check_date_range(self):
        """Refuse an end date before the start date."""
        self._check_dates()

    def action_get_category_report(self):
        """  Generate a category-based sales report.
            :return: Action to display the category-based sales report.  """
        datas = self._get_data()
        return self._get_report_action(
            'sale_report_advanced.action_sale_category', datas)

    def _get_data(self):
        """  Retrieve and format data for a category-based sales report.
            :return: A dictionary containing report data.
            :rtype: dict
            This method retrieves and formats data for a category-based sales
            report. It filters sales order lines based on optional date range
            and company selection and then categorizes the data. The resulting
            dictionary contains the report data ready for use in
            generating the report. """
        domain = [
            ('order_id.state', '!=', 'cancel'),
            ('display_type', '=', False),
            *self._get_date_domain('order_id.date_order'),
        ]
        if self.company_ids:
            domain.append(('order_id.company_id', 'in', self.company_ids.ids))
        sale_order_line = self.env['sale.order.line'].search(domain)
        category = self._get_category()
        res = self._get_category_wise(sale_order_line, category)
        if not res:
            self._raise_no_data()
        return {
            'ids': self.ids,
            'model': 'sale.report.category',
            'form': res,
            'categ_id': category,
            'start_date': self.from_date,
            'end_date': self.to_date,
        }

    def _get_category_wise(self, order_lines, category):
        """ Categorize sales data by product category.
            :param order_lines: List of sales order lines.
            :param category: List of product categories.
            :return: Categorized sales data. """
        result = []
        for cat in category:
            for lines in order_lines:
                if cat['id'] == lines.product_id.categ_id:
                    res = {
                        'so': lines.order_id.name,
                        'date': lines.order_id.date_order,
                        'product_id': lines.product_id.name,
                        'quantity': lines.product_uom_qty,
                        'tax': round(lines.price_tax, 2),
                        'uom': lines.product_id.uom_id.name,
                        'price': lines.product_id.list_price,
                        'subtotal': lines.price_subtotal,
                        'total': round(lines.price_total, 2),
                        'category_id': lines.product_id.categ_id,
                    }
                    result.append(res)
        return result

    def _get_category(self):
        """ Retrieve and format product categories.
            :return: List of product categories with IDs and names.
            :rtype: list
            This method retrieves and formats a list of product categories,
            including their IDs and names.  """
        category = []
        for rec in self.category_ids:
            data = {'id': rec,
                 'name': rec.complete_name}
            category.append(data)
        return category

    def action_get_excel_category_report(self):
        """ Generate an Excel category-based sales report.
            :return: Dictionary specifying the Excel report action.
            :rtype: dict
            This method prepares the data for an Excel category-based sales
            report and returns a dictionary
            that defines the action to generate the report in XLSX format. """
        datas = self._get_data()
        return self._get_xlsx_action(
            datas, self.env._('Sales Category Report'))

    def get_xlsx_report(self, data, response):
        """ Generate an Excel category-based sales report."""
        loaded_data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': 12})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': 20})
        txt = workbook.add_format({'font_size': 10, 'align': 'center'})
        sheet.merge_range('G2:O3', 'Sales Category Report', head)
        if loaded_data.get('start_date') and loaded_data.get('end_date'):
            sheet.write('G6', 'From:', cell_format)
            sheet.merge_range('H6:I6', loaded_data.get('start_date'), txt)
            sheet.write('M6', 'To:', cell_format)
            sheet.merge_range('N6:O6', loaded_data.get('end_date'), txt)
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#bbd5fc',
             'border': 1})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#6BA6FE', 'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#c0dbfa'})
        h_row = 7
        h_col = 10
        count = 0
        row = 5
        col = 6
        row_number = 6
        t_row = 6
        if loaded_data.get('categ_id'):
            record = loaded_data.get('categ_id')
            for rec in record:
                sheet.merge_range(h_row, h_col - 4, h_row, h_col + 4,
                                  rec['name'], format4)
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
                sheet.write(row, col, 'Tax', format2)
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
                for val in loaded_data.get('form'):
                    if val['category_id'] == rec['id']:
                        count += 1
                        column_number = 6
                        sheet.write(row_number, column_number, val['so'],
                                    format1)
                        column_number += 1
                        sheet.write(row_number, column_number, val['date'],
                                    format1)
                        sheet.set_column('H:H', 15)
                        column_number += 1
                        sheet.write(row_number, column_number,
                                    val['product_id'], format1)
                        sheet.set_column('I:I', 20)
                        column_number += 1
                        sheet.write(row_number, column_number, val['uom'],
                                    format1)
                        column_number += 1
                        sheet.write(row_number, column_number, val['quantity'],
                                    format1)
                        t_qty += val['quantity']
                        column_number += 1
                        sheet.write(row_number, column_number, val['price'],
                                    format1)
                        t_price += val['price']
                        column_number += 1
                        sheet.write(row_number, column_number, val['tax'],
                                    format1)
                        column_number += 1
                        sheet.write(row_number, column_number, val['subtotal'],
                                    format1)
                        t_subtotal += val['subtotal']
                        column_number += 1
                        sheet.write(row_number, column_number, val['total'],
                                    format1)
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
