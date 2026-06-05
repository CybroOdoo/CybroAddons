# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

import io
import json
from odoo import api, fields, models

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class FourwayReport(models.TransientModel):
    """Defines fields that needed to fetching data  for generating fourway xlsx
     report"""
    _name = "fourway.report"
    _description = "Fourway Report"

    partner_id = fields.Many2one('res.partner', string='Vendor',
                                 help="Select one or more vendors to get "
                                      "specified details")
    order_ids = fields.Many2many('purchase.order', string='Purchase Order',
                                 domain="[('partner_id', '=', partner_id)]", required=True,
                                 help="Select multiple purchase orders to "
                                      "generate report.")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        Triggered when the partner_id field changes.

        This method clears the order_ids related to the current record
        by removing all existing entries. This is useful for resetting
        the order list when a new partner is selected, ensuring that
        only relevant orders are displayed for the selected partner.

        :return: None
        """
        self.order_ids = [(5, 0, 0)]

    def print_xlsx(self):
        """Action for printing xlsx fourway report"""
        data = {
            'partner_id': self.partner_id.id,
            'order_ids': self.order_ids.ids,
        }
        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'fourway.report',
                'options': json.dumps(data),
                'output_format': 'xlsx',
                'report_name': 'Four Way Matching Report',
            },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Generating the XLSX report based on selected fields"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_row(9, 30)
        # Set the width of the columns
        column_widths = [10, 13, 10, 13, 17, 10, 10, 10, 10, 15, 10, 11, 10, 17,
                         12, 12, 18, 10, 12]
        for i, width in enumerate(column_widths):
            sheet.set_column(i, i, width)
        cell_format = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'bg_color': '#AAAAAA', 'text_wrap': True})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px', })
        sheet.merge_range('B2:I3', '4WAY MATCHING PO REPORT', head)

        # Write column headers
        headers = ['PURCHASE ORDER', 'VENDOR', 'PO DATE', 'PRODUCT CODE',
                   'DESCRIPTION', 'UNIT PRICE', 'ORDER QTY', 'TAX AMOUNT',
                   'AMOUNT TOTAL', 'REFERENCE', 'VALIDATE DATE',
                   'DESTINATION LOCATION', 'QUANTITY', 'BILL', 'BILL DATE',
                   'BILL AMOUNT', 'PAYMENT NUMBER', 'PAYMENT DATE',
                   'PAYMENT AMOUNT']
        for i, header in enumerate(headers):
            sheet.write(9, i, header, cell_format)

        purchase = self.env['purchase.order'].browse(data['order_ids'])
        purchase_orderline = purchase.mapped('order_line')
        row = 10
        for rec in purchase_orderline:
            sheet.write(row, 0, rec.order_id.name)
            sheet.write(row, 1, rec.order_id.partner_id.name)
            sheet.write(row, 2, str(rec.order_id.date_order.date()))
            sheet.write(row, 3, rec.product_id.default_code)
            sheet.write(row, 4, rec.product_id.name)
            sheet.write(row, 5, float(rec.price_unit))
            sheet.write(row, 6, rec.product_qty)
            sheet.write(row, 7, float(rec.price_tax))
            sheet.write(row, 8, float(rec.price_total))
            row += 1

            # Moves
            if rec.move_ids:
                for move in rec.move_ids:
                    sheet.write(row, 9, move.picking_id.name)
                    if move.picking_id.state == 'done':
                        sheet.write(row, 10,
                                    str(move.picking_id.date_done.date()))
                        sheet.write(row, 11, move.location_dest_id.display_name)
                        sheet.write(row, 12, move.quantity)
                    row += 1

            # Invoice lines
            if rec.invoice_lines:
                for bill_line in rec.invoice_lines:
                    sheet.write(row, 13, bill_line.move_id.name)
                    sheet.write(row, 14, str(bill_line.move_id.date))
                    sheet.write(row, 15, float(bill_line.price_total))
                    row += 1
                    payments = self.env['account.payment'].search([]).filtered(
                        lambda
                            x: bill_line.move_id.id in x.reconciled_bill_ids.ids)
                    if payments:
                        for pay in payments:
                            sheet.write(row, 16, pay.name)
                            sheet.write(row, 17, str(pay.date))
                            sheet.write(row, 18, float(pay.amount))
                            row += 1
                    else:
                        row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
