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


class SaleReportInvoice(models.TransientModel):
    """ Model for handling sales report invoices.
        This transient model is used for managing data related to sales
        report invoices. """
    _name = "sale.report.invoice"
    _inherit = 'sale.report.mixin'
    _description = 'Invoice Analysis Report'

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
        default='open', required=True,
        help="Select the status of the invoices to include in the report.")
    company_ids = fields.Many2many('res.company', string='Companies',
                                   help="Select one or more companies for "
                                        "the report.")
    today_date = fields.Date(default=fields.Date.context_today,
                             help="Automatically set to the current date.")

    def action_get_invoice_report(self):
        """ Generate an invoice analysis report.
            :return: Action to display the invoice analysis report. """
        datas = self._get_data()
        return self._get_report_action(
            'sale_report_advanced.action_invoice_analysis', datas)

    def _get_invoices(self, order):
        """Return the posted invoices of the order for the selected status."""
        invoices = order.invoice_ids.filtered(
            lambda move: move.state == 'posted')
        paid = invoices.filtered(
            lambda move: move.payment_state in ('paid', 'in_payment'))
        if self.status == 'open':
            return invoices - paid
        if self.status == 'paid':
            return paid
        return invoices

    def _get_data(self):
        """Get report values for sale invoice report """
        domain = [
            ('state', '!=', 'cancel'),
            ('partner_id', 'in', self.customer_ids.ids),
            *self._get_date_domain('date_order'),
        ]
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))
        result = []
        for order in self.env['sale.order'].search(domain):
            for invoice in self._get_invoices(order):
                result.append({
                    'so': order.name,
                    'partner_id': order.partner_id,
                    'order_date': order.date_order,
                    'invoice': invoice.name,
                    'date': invoice.invoice_date,
                    'invoiced': invoice.amount_total,
                    'paid': invoice.amount_total - invoice.amount_residual,
                    'due': invoice.amount_residual,
                })
        if not result:
            self._raise_no_data()
        customers = [{'id': rec, 'name': rec.name}
                     for rec in self.customer_ids]
        return {
            'ids': self.ids,
            'model': 'sale.report.invoice',
            'form': result,
            'partner_id': customers,
            'start_date': self.from_date,
            'end_date': self.to_date,
            'status': self.status,
        }

    def action_get_excel_invoice_report(self):
        """ Generate an Excel invoice analysis report.
            :return: Action to create the Excel report.  """
        datas = self._get_data()
        return self._get_xlsx_action(
            datas, self.env._('Invoice Analysis Report'))

    def get_xlsx_report(self, data, response):
        """ Generate an Excel invoice analysis report. """
        loaded_data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': 12})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': 20})
        txt = workbook.add_format({'font_size': 10, 'align': 'center'})
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
