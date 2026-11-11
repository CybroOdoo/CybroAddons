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


class SaleReportWeekly(models.TransientModel):
    """ Model for handling sales report in weekly .
    This transient model is used for managing data related to sales
    report invoices. """
    _name = "sale.report.weekly"
    _inherit = 'sale.report.mixin'
    _description = 'Hourly Sales Report'

    date = fields.Date(required=True,
                       help="Select the date of the report")
    invoice_status = fields.Selection(
        [('invoiced', 'Fully Invoiced'),
         ('to invoice', 'To Invoice'),
         ('upselling', 'Upselling Opportunity'),
         ('no', 'Nothing to Invoice')],
        default='no', required=True,
        help='Select the invoice status for this record. '
             'Fully Invoiced: All invoices are fully paid. '
             'To Invoice: There are pending invoices. '
             'Upselling Opportunity: More was delivered than ordered. '
             'Nothing to Invoice: No invoices are related to this record.')
    amount_type = fields.Selection(
        [('total', 'Total Amount'), ('untax', 'Untaxed Amount')],
        string='Total Amount', default='total',
        help='Select the type of amount to be used. '
             'Total Amount: Includes taxes. '
             'Untaxed Amount: Excludes taxes.')
    today_date = fields.Date(
        default=fields.Date.context_today,
        help='This field is automatically set to the current date.')

    def action_get_weekly_report(self):
        """Generates and displays a weekly sales report."""
        datas = self._get_data()
        return self._get_report_action(
            'sale_report_advanced.action_sales_weekly', datas)

    def _get_data(self):
        """ Function for getting data for report """
        times = {
            'night': self.env._('Night (00:00-05:00)'),
            'morning': self.env._('Morning (05:00-12:00)'),
            'noon': self.env._('Noon (12:00-17:00)'),
            'evening': self.env._('Evening (17:00-24:00)'),
        }
        sale_orders = self.env['sale.order'].search([
            ('invoice_status', '=', self.invoice_status),
            ('date_order', '>=', self.date),
            ('state', '!=', 'cancel'),
        ])
        result = []
        for order in sale_orders:
            ordered_at = fields.Datetime.context_timestamp(
                self, order.date_order)
            result.append({
                'order': order.name,
                'amount': (order.amount_total if self.amount_type == 'total'
                           else order.amount_untaxed),
                'time': self._get_time_id(ordered_at.hour),
                'date': ordered_at.date(),
            })
        if not result:
            self._raise_no_data()
        return {
            'ids': self.ids,
            'model': 'sale.report.weekly',
            'form': result,
            'date': self.date,
            'type': self.amount_type,
            'times': times,
        }

    def _get_time_id(self, hour):
        """Return the part of the day of an hour."""
        if hour < 5:
            return 'night'
        if hour < 12:
            return 'morning'
        return 'noon' if hour < 17 else 'evening'

    def action_get_excel_weekly_report(self):
        """Generate and return a configuration dictionary for an Excel
        weekly report."""
        datas = self._get_data()
        return self._get_xlsx_action(
            datas, self.env._('Hourly Sales Report'))

    def get_xlsx_report(self, data, response):
        """ Function for generating xlsx report """
        loaded_data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': 20})
        sheet.merge_range('G2:I3', 'Hourly Sales Report', head)
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#f5f9ff',
             'border': 1})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#6BA6FE', 'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#95ff63', 'border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'border': 1})
        h_row = 7
        h_col = 7
        count = 0
        row = 4
        row_number = 5
        for rec in loaded_data['times']:
            col = 6
            row = row + count + 4
            sheet.merge_range(h_row, h_col - 1, h_row, h_col + 1,
                              loaded_data['times'][rec], format3)
            sheet.write(row, col, 'Order', format2)
            sheet.set_column(row, col, 15)
            col += 1
            sheet.write(row, col, 'Date', format2)
            sheet.set_column(row, col, 15)
            col += 1
            if loaded_data['type'] == 'total':
                sheet.write(row, col, 'Total', format2)
                sheet.set_column(row, col, 15)
                col += 1
            else:
                sheet.write(row, col, 'Untaxed Total', format2)
                sheet.set_column(row, col, 15)
                col += 1
            t_total = 0
            row_number = row_number + 4
            count = 0
            t_col = 7
            for val in loaded_data['form']:
                if val['time'] == rec:
                    count += 1
                    column_number = 6
                    sheet.write(row_number, column_number, val['order'],
                                format1)
                    sheet.set_column(row_number, column_number, 15)
                    column_number += 1
                    sheet.write(row_number, column_number, val['date'], format1)
                    sheet.set_column(row_number, column_number, 15)
                    column_number += 1
                    sheet.write(row_number, column_number, val['amount'],
                                format1)
                    t_total += val['amount']
                    sheet.set_column(row_number, column_number, 15)
                    row_number += 1
            sheet.write(row_number, t_col, 'Total', format4)
            sheet.set_column(row_number, t_col, 15)
            t_col += 1
            sheet.write(row_number, t_col, t_total, format4)
            h_row = h_row + count + 4
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
