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


class SaleReportAnalysis(models.TransientModel):
    """Model for Sale report analysis """
    _name = "sale.report.analysis"
    _inherit = 'sale.report.mixin'
    _description = 'Sales Analysis Report'

    customer_ids = fields.Many2many('res.partner', string="Customers",
                                    required=True,
                                    help='Select the customers of sales')
    product_ids = fields.Many2many('product.product', string='Products',
                                   help="Select products of sale report")
    from_date = fields.Date(string="Start Date", help='Start date of report')
    to_date = fields.Date(string="End Date", help="End date of report")
    status = fields.Selection(
        [('all', 'All'), ('draft', 'Draft'), ('sent', 'Quotation Sent'),
         ('sale', 'Sale Order')],
        default='all', required=True,
        help="Select the status of sale order")
    print_type = fields.Selection(
        [('sale', 'Sale Order'), ('product', 'Products')],
        string='Print By', default='sale', required=True,
        help='Select the type of print: "Sale Order" or "Products".')
    today_date = fields.Date(string="Date", default=fields.Date.context_today,
                             help="Date of the report")

    @api.constrains('from_date', 'to_date')
    def _check_date_range(self):
        """Refuse an end date before the start date."""
        self._check_dates()

    def action_get_analysis_report(self):
        """ Generate a sales analysis report.
            :return: Action to display the sales analysis report. """
        datas = self._get_data()
        return self._get_report_action(
            'sale_report_advanced.action_sales_analysis', datas)

    def _get_data(self):
        """ Retrieve and format data for a sales analysis report.
            :return: Formatted data for the report. """
        result = []
        if self.print_type == 'sale':
            for rec in self.env['sale.order'].search(self._get_order_domain()):
                paid = self._get_total_paid_amount(rec.invoice_ids)
                result.append({
                    'so': rec.name,
                    'date': rec.date_order,
                    'sales_person': rec.user_id.name,
                    's_amt': rec.amount_total,
                    'p_amt': paid,
                    'balance': rec.amount_total - paid,
                    'partner_id': rec.partner_id,
                })
        else:
            domain = [('order_id', 'any', self._get_order_domain()),
                      ('display_type', '=', False)]
            if self.product_ids:
                domain.append(('product_id', 'in', self.product_ids.ids))
            for rec in self.env['sale.order.line'].search(domain):
                result.append({
                    'so': rec.order_id.name,
                    'date': rec.order_id.date_order,
                    'product_id': rec.product_id.name,
                    'price': rec.product_id.list_price,
                    'quantity': rec.product_uom_qty,
                    'discount': rec.discount,
                    'tax': round(rec.price_tax, 2),
                    'total': round(rec.price_total, 2),
                    'partner_id': rec.order_id.partner_id,
                })
        if not result:
            self._raise_no_data()
        return {
            'ids': self.ids,
            'model': 'sale.report.analysis',
            'form': result,
            'partner_id': self._get_customers(),
            'start_date': self.from_date,
            'end_date': self.to_date,
            'type': self.print_type,
        }

    def _get_total_paid_amount(self, invoices):
        """ Calculate the total paid amount from a list of invoices.
            :return: Total paid amount. """
        total = 0
        for inv in invoices:
            if inv.payment_state == 'paid':
                total += inv.amount_total
        return total

    def _get_order_domain(self):
        """Return the domain of the sale orders of the report."""
        domain = [('state', '!=', 'cancel'),
                  ('partner_id', 'in', self.customer_ids.ids),
                  *self._get_date_domain('date_order')]
        if self.status != 'all':
            domain.append(('state', '=', self.status))
        return domain

    def _get_customers(self):
        """ Retrieve customer data.
            :return: List of customer information.
            :rtype: list
            This method retrieves customer data and returns a list of customer
            information, including their ID and name. """
        customers = []
        for rec in self.customer_ids:
            data = {'id': rec,
                    'name': rec.name}
            customers.append(data)
        return customers

    def action_get_excel_analysis_report(self):
        """ Generate an Excel analysis report.
           :return: Dictionary specifying the Excel report action.
           :rtype: dict
           This method prepares the data for an Excel analysis report and
           returns a dictionary that defines the action to generate the
           report in XLSX format. """
        datas = self._get_data()
        return self._get_xlsx_action(
            datas, self.env._('Sales Analysis Report'))

    def get_xlsx_report(self, data, response):
        """Function for generating an Excel analysis report"""
        loaded_data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        record = []
        cell_format = workbook.add_format({'font_size': 12})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': 20})
        txt = workbook.add_format({'font_size': 10, 'align': 'center'})
        if loaded_data.get('type') == 'sale':
            sheet.merge_range('G2:L3', 'Sales Analysis Report', head)
            if loaded_data.get('start_date') and loaded_data.get('end_date'):
                sheet.write('G6', 'From:', cell_format)
                sheet.merge_range('H6:I6', loaded_data.get('start_date'), txt)
                sheet.write('J6', 'To:', cell_format)
                sheet.merge_range('K6:L6', loaded_data.get('end_date'), txt)
            h_col = 9
        else:
            sheet.merge_range('G2:N3', 'Sales Analysis Report', head)
            if loaded_data.get('start_date') and loaded_data.get('end_date'):
                sheet.write('G6', 'From:', cell_format)
                sheet.merge_range('H6:I6', loaded_data.get('start_date'), txt)
                sheet.write('K6', 'To:', cell_format)
                sheet.merge_range('L6:N6', loaded_data.get('end_date'), txt)
            h_col = 10
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#f5f9ff',
             'border': 1})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#6BA6FE', 'border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True})
        if loaded_data.get('partner_id'):
            record = loaded_data.get('partner_id')
        h_row = 7
        count = 0
        row = 5
        row_number = 6
        t_row = 6
        for rec in record:
            if loaded_data.get('type') == 'sale':
                sheet.merge_range(h_row, h_col - 3, h_row, h_col + 2,
                                  rec['name'], format1)
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
                count = 0
                row_number = row_number + count + 3
                t_samt = 0
                t_pamt = 0
                t_bal = 0
                t_col = 8
                for val in loaded_data.get('form'):
                    if val['partner_id'] == rec['id']:
                        count += 1
                        column_number = 6
                        sheet.write(row_number, column_number, val['so'],
                                    format1)
                        column_number += 1
                        sheet.write(row_number, column_number, val['date'],
                                    format1)
                        sheet.set_column('H:H', 17)
                        column_number += 1
                        sheet.write(row_number, column_number,
                                    val['sales_person'], format1)
                        sheet.set_column('I:I', 15)
                        column_number += 1
                        sheet.write(row_number, column_number, val['s_amt'],
                                    format1)
                        sheet.set_column('J:J', 13)
                        t_samt += val['s_amt']
                        column_number += 1
                        sheet.write(row_number, column_number, val['p_amt'],
                                    format1)
                        sheet.set_column('K:K', 12)
                        t_pamt += val['p_amt']
                        column_number += 1
                        sheet.write(row_number, column_number, val['balance'],
                                    format1)
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
            if loaded_data.get('type') == 'product':
                sheet.merge_range(h_row, h_col - 4, h_row, h_col + 3,
                                  rec['name'], format1)
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
                sheet.write(row, col, 'Tax', format2)
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
                for val in loaded_data.get('form'):
                    if val['partner_id'] == rec['id']:
                        count += 1
                        column_number = 6
                        sheet.write(row_number, column_number, val['so'],
                                    format1)
                        column_number += 1
                        sheet.write(row_number, column_number, val['date'],
                                    format1)
                        sheet.set_column('H:H', 17)
                        column_number += 1
                        sheet.write(row_number, column_number,
                                    val['product_id'], format1)
                        sheet.set_column('I:I', 17)
                        column_number += 1
                        sheet.write(row_number, column_number, val['quantity'],
                                    format1)
                        sheet.set_column('J:J', 7)
                        t_qty += val['quantity']
                        column_number += 1
                        sheet.write(row_number, column_number, val['price'],
                                    format1)
                        sheet.set_column('K:K', 12)
                        t_price += val['price']
                        column_number += 1
                        sheet.write(row_number, column_number, val['discount'],
                                    format1)
                        sheet.set_column('L:L', 12)
                        column_number += 1
                        sheet.write(row_number, column_number, val['tax'],
                                    format1)
                        sheet.set_column('M:M', 10)
                        t_tax += val['tax']
                        column_number += 1
                        sheet.write(row_number, column_number, val['total'],
                                    format1)
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
