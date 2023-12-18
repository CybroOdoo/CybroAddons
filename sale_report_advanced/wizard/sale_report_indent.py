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


class SaleReportIndent(models.TransientModel):
    """ Model for handling sales report indents.
        This transient model is used for managing data related to sales
        report indents. It is designed for
        temporary and intermediary data storage and is not intended for
        permanent database storage.  """
    _name = "sale.report.indent"
    _description = "Sale Report Indent"

    customer_ids = fields.Many2many('res.partner', string="Customers",
                                    required=True, help="Select one or more"
                                                        " customers for the report.")
    category_ids = fields.Many2many('product.category', string="Categories",
                                    required=True,
                                    help="Select one or more product categories.")
    from_date = fields.Date(string="Start Date",
                            help="Specify the beginning date for your report.")
    to_date = fields.Date(string="End Date",
                          help="Specify the ending date for your report.")
    status = fields.Selection(
        [('all', 'All'), ('draft', 'Draft'), ('sent', 'Quotation Sent'),
         ('sale', 'Sale Order'), ('done', 'Locked')],
        string='Status', default='all', required=True,
        help="Select the status of the orders to include in the report.")
    company_ids = fields.Many2many('res.company', string='Companies',
                                   help="Select one or more companies"
                                        " for the report.")
    today_date = fields.Date(default=fields.Date.today(),
                             help="Automatically set to the current date.")

    def action_get_indent_report(self):
        """ Generate a category-based sales report.
            :return: Action to display the category-based sales report. """
        datas = self._get_data()
        return self.env.ref(
            'sale_report_advanced.action_sale_indent').report_action([],
                                                                     data=datas)

    def _get_data(self):
        """ Retrieve and format data for a sales report.
            :return: A dictionary containing report data.
            :rtype: dict
            This method retrieves and formats data for a sales report.
            It filters sales order lines based on optional date
            range and company selection, then categorizes the data using the
            '_get_orders' method. The resulting dictionary
            contains the report data ready for use in generating the report.
            It includes information such as order details,
            product categories, customers, start and end dates.
            """
        domain = [('order_id.state', '!=', 'cancel')]
        if self.from_date:
            domain.append(('order_id.date_order', '>=', self.from_date))
        elif self.to_date:
            domain.append(('order_id.date_order', '<=', self.to_date))
        elif self.company_ids:
            domain.append(('order_id.company_id', 'in', self.company_ids))
        sale_order_line = self.env['sale.order.line'].search(domain)
        res = self._get_orders(sale_order_line)
        if not res:
            raise ValidationError("No data available for printing.")
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
        """ Filter and categorize sales orders.
            :param sale_order_line: List of sales order lines.
            :return: Categorized sales orders. """
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
        """ Categorize sales data by customer and category.
            :param order: List of sales orders.
            :return: Categorized sales data. """
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
        """ Retrieve and format product categories.
            :return: List of product categories with IDs and names. """
        category = []
        for rec in self.category_ids:
            data = {
                'id': rec,
                'name': rec.complete_name
            }
            category.append(data)
        return category

    def _get_customers(self):
        """ Retrieve and format customer data.
           :return: List of customer information with IDs and names. """
        customers = []
        for rec in self.customer_ids:
            data = {
                'id': rec,
                'name': rec.name
            }
            customers.append(data)
        return customers

    def action_get_excel_indent_report(self):
        """ Generate an Excel category-based sales report.
            :return: Dictionary specifying the Excel report action.
            """
        datas = self._get_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'sale.report.indent',
                     'output_format': 'xlsx',
                     'options': json.dumps(datas,
                                           default=date_utils.json_default),
                     'report_name': 'Sales Indent Report',
                     },
        }

    def get_xlsx_report(self, data, response):
        """ Generate an Excel category-based sales report. """
        loaded_data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px', })
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        sheet.merge_range('G2:N3', 'Product Sales Indent Report', head)
        if loaded_data.get('start_date') and loaded_data.get('end_date'):
            sheet.write('H6', 'From:', cell_format)
            sheet.merge_range('I6:J6', loaded_data.get('start_date'), txt)
            sheet.write('K6', 'To:', cell_format)
            sheet.merge_range('L6:M6', loaded_data.get('end_date'), txt)
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#f5f9ff',
             'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#6BA6FE', 'border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#b6d0fa', 'border': 1})
        if loaded_data.get('categ_id'):
            categ = loaded_data.get('categ_id')
        if loaded_data.get('partner_id'):
            partner = loaded_data.get('partner_id')
        h_row = 6
        h_col = 12
        c_row = 6
        row = 7
        row_number = 6
        for rec in partner:
            count = 0
            h_row += 1
            sheet.merge_range(h_row, h_col - 5, h_row, h_col, rec['name'],
                              format3)
            c_row = c_row + 2
            row += 2
            row_number += 2
            for cat in categ:
                count += 2
                c_col = 12
                col = 9
                sheet.merge_range(c_row, c_col-5, c_row, c_col, cat['name'],
                                  format1)
                sheet.merge_range(row, c_col-5,row, c_col, 'Product', format4)
                sheet.set_column('J:J', 17)
                col += 1
                sheet.merge_range(row, c_col-5, row, c_col, 'Quantity', format4)
                sheet.set_column('K:K', 17)
                row_number += 2
                c_count = 0
                for val in loaded_data.get('form'):
                    if val['category_id'] == cat['id'] and val['partner_id'] == rec['id']:
                        c_count += 1
                        count += 1
                        column_number = 9
                        column_number1 = 12
                        sheet.merge_range(row_number, column_number-2,row_number, column_number,
                                    val['product_id'], format1)
                        sheet.set_column('J:J', 17)
                        column_number += 1
                        sheet.merge_range(row_number, column_number1-2, row_number, column_number1, val['quantity'],
                                    format1)
                        sheet.set_column('K:K', 17)
                        row_number += 1
                row = row + c_count + 2
                c_row = c_row + c_count + 2
            h_row = h_row + count + 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
