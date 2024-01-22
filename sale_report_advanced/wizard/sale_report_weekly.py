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
from odoo import fields, models, _
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class SaleReportWeekly(models.TransientModel):
    """ Model for handling sales report in weekly .
    This transient model is used for managing data related to sales
    report invoices. """
    _name = "sale.report.weekly"
    _description = 'Sales Report Weekly'

    date = fields.Date(string='Date', required=True,
                       help="Select the date of the report")
    invoice_status = fields.Selection(
        [('invoiced', 'Fully Invoiced'),
         ('to invoice', 'To Invoice'),
         ('no', 'Nothing to Invoice')],
        string='Invoice Status', default='no', required=True,
        help='Select the invoice status for this record. '
             'Fully Invoiced: All invoices are fully paid. '
             'To Invoice: There are pending invoices. '
             'Nothing to Invoice: No invoices are related to this record.')
    amount_type = fields.Selection(
        [('total', 'Total Amount'), ('untax', 'Untaxed Amount')],
        string='Total Amount', default='total',
        help='Select the type of amount to be used. '
             'Total Amount: Includes taxes. '
             'Untaxed Amount: Excludes taxes.')
    today_date = fields.Date(
        default=fields.Date.today(),
        help='This field is automatically set to the current date.')

    def action_get_weekly_report(self):
        """Generates and displays a weekly sales report."""
        datas = self._get_data()
        return self.env.ref(
            'sale_report_advanced.action_sales_weekly').report_action([],
                                                        data=datas)

    def _get_data(self):
        """ Function for getting data for report """
        result = []
        times = {'morning': 'Morning (5:00-12:00)',
                 'noon': 'Noon (1:00-17:00)',
                 'evening': 'Evening (18:00-23:00)'}
        sale_orders = self.env['sale.order'].sudo().search([
            ('invoice_status', '=', self.invoice_status),
            ('date_order', '>=', self.date),
            ('state', '!=', 'cancel')
        ])
        if not sale_orders:
            raise ValidationError("No data available for printing.")
        for rec in sale_orders:
            if self.amount_type == 'total':
                amount = rec.amount_total
            else:
                amount = rec.amount_untaxed
            for time_id, time_name in times.items():
                if rec.date_order.hour > self._get_time_start(
                        time_id) and rec.date_order.hour <= self._get_time_end(
                        time_id):
                    res = {
                        'order': rec.name,
                        'amount': amount,
                        'time': time_id,
                        'date': rec.date_order.date()
                    }
                    result.append(res)
        if not result:
            raise ValidationError("No data available for printing.")
        datas = {
            'ids': self,
            'model': 'sale.report.weekly',
            'form': result,
            'date': self.date,
            'type': self.amount_type,
            'times': times
        }
        return datas

    def _get_time_start(self, time_id):
        """Get the starting hour corresponding to a given time identifier."""
        time_mapping = {'morning': 5, 'noon': 12, 'evening': 17}
        return time_mapping[time_id]

    def _get_time_end(self, time_id):
        """Get the ending hour corresponding to a given time identifier."""
        time_mapping = {'morning': 12, 'noon': 17, 'evening': 23}
        return time_mapping[time_id]

    def action_get_excel_weekly_report(self):
        """Generate and return a configuration dictionary for an Excel
        weekly report."""
        datas = self._get_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'sale.report.weekly',
                     'output_format': 'xlsx',
                     'options': json.dumps(datas,
                                           default=date_utils.json_default),
                     'report_name': 'Sale Hourly Report',
                     },
        }

    def get_xlsx_report(self, data, response):
        """ Function for generating xlsx report """
        loaded_data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
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
            sheet.merge_range(h_row, h_col - 1, h_row, h_col + 1, rec,
                              format3)
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
