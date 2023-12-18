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


class SaleReportInvoice(models.TransientModel):
    """ Model for handling sales report invoices.
        This transient model is used for managing data related to sales
        report invoices. """
    _name = "sale.report.invoice"
    _description = 'Sales Report Invoices'

    customer_ids = fields.Many2many('res.partner',
                                    string="Customers", required=True,
                                    help="Select one or more customers for "
                                         "the report.")
    from_date = fields.Date(string="Start Date",
                            help="Specify the beginning date for your report.")
    to_date = fields.Date(string="End Date",
                          help="Specify the ending date for your report.")
    status = fields.Selection(
        [('open', 'Open'), ('paid', 'Paid'), ('both', 'Both')],
        string='Status', default='open', required=True,
        help="Select the status of the invoices to include in the report.")
    company_ids = fields.Many2many('res.company', string='Companies',
                                   help="Select one or more companies for "
                                        "the report.")
    today_date = fields.Date(default=fields.Date.today(),
                             help="Automatically set to the current date.")

    def action_get_invoice_report(self):
        """ Generate an invoice analysis report.
            :return: Action to display the invoice analysis report. """
        datas = self._get_data()
        return self.env.ref(
            'sale_report_advanced.action_invoice_analysis').report_action([],
                                                                          data=datas)

    def _get_data(self):
        """Get report values for sale invoice report """
        domain = [('state', '!=', 'cancel')]
        if self.from_date:
            domain.append(('date_order', '>=', self.from_date))
        if self.to_date:
            domain.append(('date_order', '<=', self.to_date))
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids))
        sales_order = self.env['sale.order'].search(domain)
        if not sales_order:
            raise ValidationError("No data available for printing.")
        result = []
        customers = []
        for record in self.customer_ids:
            data = {
                'id': record,
                'name': record.name
            }
            customers.append(data)
        for so in sales_order:
            for cust in customers:
                if cust['id'] == so['partner_id'] and so.invoice_ids:
                    if self.status == 'open':
                        for inv in so.invoice_ids:
                            if inv.payment_state != 'paid':
                                res = {
                                    'so': so.name,
                                    'partner_id': so.partner_id,
                                    'order_date': so.date_order,
                                    'invoice': inv.name,
                                    'date': inv.invoice_date,
                                    'invoiced': inv.amount_total,
                                    'paid': inv.amount_total - inv.amount_residual,
                                    'due': inv.amount_residual,
                                }
                                result.append(res)
                    elif self.status == 'paid':
                        for inv in so.invoice_ids:
                            if inv.payment_state == 'paid':
                                res = {
                                    'so': so.name,
                                    'partner_id': so.partner_id,
                                    'order_date': so.date_order,
                                    'invoice': inv.name,
                                    'date': inv.invoice_date,
                                    'invoiced': inv.amount_total,
                                    'paid': inv.amount_total - inv.amount_residual,
                                    'due': inv.amount_residual,
                                }
                                result.append(res)
                    else:
                        for inv in so.invoice_ids:
                            res = {
                                'so': so.name,
                                'partner_id': so.partner_id,
                                'order_date': so.date_order,
                                'invoice': inv.name,
                                'date': inv.invoice_date,
                                'invoiced': inv.amount_total,
                                'paid': inv.amount_total - inv.amount_residual,
                                'due': inv.amount_residual,
                            }
                            result.append(res)
        if not result:
            raise ValidationError("No data available for printing.")
        datas = {
            'ids': self,
            'model': 'sale.report.invoice',
            'form': result,
            'partner_id': customers,
            'start_date': self.from_date,
            'end_date': self.to_date,
            'status': self.status,
        }
        return datas

    def action_get_excel_invoice_report(self):
        """ Generate an Excel invoice analysis report.
            :return: Action to create the Excel report.  """
        datas = self._get_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'sale.report.invoice',
                     'output_format': 'xlsx',
                     'options': json.dumps(datas,
                                           default=date_utils.json_default),
                     'report_name': 'Sale Invoice Report',
                     },
        }

    def get_xlsx_report(self, data, response):
        """ Generate an Excel invoice analysis report. """
        loaded_data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px', })
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        sheet.merge_range('G2:M3', 'Invoice Analysis Report', head)
        if loaded_data.get('start_date') and loaded_data.get('end_date'):
            sheet.write('G6', 'From:', cell_format)
            sheet.merge_range('H6:I6', loaded_data.get('start_date'), txt)
            sheet.write('K6', 'To:', cell_format)
            sheet.merge_range('L6:M6', loaded_data.get('end_date'), txt)
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'bg_color': '#bbd5fc',
             'border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#bbd5fc',
             'border': 1})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#6BA6FE', 'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True})
        record = loaded_data.get('partner_id')
        h_row = 7
        h_col = 9
        count = 0
        row = 5
        col = 6
        row_number = 6
        t_row = 6
        if loaded_data.get('partner_id'):
            for rec in record:
                sheet.merge_range(h_row, h_col - 3, h_row, h_col + 3,
                                  rec['name'], format4)
                row = row + count + 3
                sheet.write(row, col, 'Order Number', format2)
                sheet.set_column('G:G', 12)
                col += 1
                sheet.write(row, col, 'Order Date', format2)
                sheet.set_column('H:H', 15)
                col += 1
                sheet.write(row, col, 'Invoice Number', format2)
                sheet.set_column('I:I', 13)
                col += 1
                sheet.write(row, col, 'Invoice Date', format2)
                sheet.set_column('J:J', 15)
                col += 1
                sheet.write(row, col, 'Amount Invoiced', format2)
                sheet.set_column('K:K', 11)
                col += 1
                sheet.write(row, col, 'Amount Paid', format2)
                sheet.set_column('L:L', 11)
                col += 1
                sheet.write(row, col, 'Amount Due', format2)
                sheet.set_column('M:M', 11)
                col += 1
                col = 6
                count = 0
                t_invoiced = 0
                t_paid = 0
                t_due = 0
                row_number = row_number + count + 3
                t_col = 9
                for val in loaded_data.get('form'):
                    if val['partner_id'] == rec['id']:
                        count += 1
                        column_number = 6
                        sheet.write(row_number, column_number, val['so'],
                                    format1)
                        sheet.set_column('G:G', 12)
                        column_number += 1
                        sheet.write(row_number, column_number,
                                    val['order_date'], format1)
                        sheet.set_column('H:H', 15)
                        column_number += 1
                        sheet.write(row_number, column_number, val['invoice'],
                                    format1)
                        sheet.set_column('I:I', 13)
                        column_number += 1
                        sheet.write(row_number, column_number, val['date'],
                                    format1)
                        sheet.set_column('J:J', 15)
                        column_number += 1
                        sheet.write(row_number, column_number, val['invoiced'],
                                    format1)
                        sheet.set_column('K:K', 14)
                        t_invoiced += val['invoiced']
                        column_number += 1
                        sheet.write(row_number, column_number, val['paid'],
                                    format1)
                        sheet.set_column('L:L', 11)
                        t_paid += val['paid']
                        column_number += 1
                        sheet.write(row_number, column_number, val['due'],
                                    format1)
                        sheet.set_column('M:M', 11)
                        t_due += val['due']
                        row_number += 1
                t_row = t_row + count + 3
                sheet.write(t_row, t_col, 'Total', format3)
                sheet.set_column('J:J', 15)
                t_col += 1
                sheet.write(t_row, t_col, t_invoiced, format3)
                sheet.set_column('K:K', 14)
                t_col += 1
                sheet.write(t_row, t_col, t_paid, format3)
                sheet.set_column('L:L', 11)
                t_col += 1
                sheet.write(t_row, t_col, t_due, format3)
                sheet.set_column('M:M', 11)
                h_row = h_row + count + 3
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
