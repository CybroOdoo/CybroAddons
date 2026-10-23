# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
import io
import json
from odoo import api, fields, models

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class FourwayReport(models.TransientModel):
    """Defines fields needed for fetching data to generate the four-way
    XLSX report."""
    _name = "fourway.report"
    _description = "Fourway Report"

    partner_id = fields.Many2one('res.partner', string='Vendor',
                                  help="Select one or more vendors to get "
                                       "specified details")
    order_ids = fields.Many2many('purchase.order', string='Purchase Order',
                                 domain="[('partner_id', '=', partner_id)]",
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

    def get_xlsx_report(self, data, response=None):
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

        order_ids = data.get('order_ids') or []
        partner_id = data.get('partner_id')
        # Exclude draft and cancelled purchase orders
        valid_states = [('state', 'not in', ('draft', 'cancel'))]
        if order_ids:
            purchase = self.env['purchase.order'].browse(order_ids).filtered(
                lambda po: po.state not in ('draft', 'cancel'))
        elif partner_id:
            purchase = self.env['purchase.order'].search(
                [('partner_id', '=', partner_id)] + valid_states)
        else:
            purchase = self.env['purchase.order'].search(valid_states)

        purchase_orderline = purchase.mapped('order_line')
        row = 10
        for rec in purchase_orderline:
            sheet.write(row, 0, rec.order_id.name or '')
            sheet.write(row, 1, rec.order_id.partner_id.name or '')
            sheet.write(row, 2, str(rec.order_id.date_order.date()) if rec.order_id.date_order else '')
            sheet.write(row, 3, rec.product_id.default_code or '')
            sheet.write(row, 4, rec.product_id.name or '')
            sheet.write(row, 5, float(rec.price_unit))
            sheet.write(row, 6, rec.product_qty)
            sheet.write(row, 7, float(rec.price_tax))
            sheet.write(row, 8, float(rec.price_total))
            row += 1

            # Moves - only include validated (done) moves
            moves = getattr(rec, 'move_ids', False)
            if moves:
                done_moves = moves.filtered(
                    lambda m: m.picking_id and m.picking_id.state == 'done')
                for move in done_moves:
                    sheet.write(row, 9, move.picking_id.name or '')
                    sheet.write(row, 10,
                                str(move.picking_id.date_done.date()) if move.picking_id.date_done else '')
                    sheet.write(row, 11, move.location_dest_id.display_name or '')
                    sheet.write(row, 12, getattr(move, 'quantity', getattr(move, 'product_uom_qty', 0.0)))
                    row += 1

            # Invoice lines
            invoice_lines = getattr(rec, 'invoice_lines', False)
            if invoice_lines:
                for bill_line in invoice_lines:
                    sheet.write(row, 13, bill_line.move_id.name or '')
                    sheet.write(row, 14, str(bill_line.move_id.date) if bill_line.move_id.date else '')
                    sheet.write(row, 15, float(bill_line.price_total))
                    payments = getattr(bill_line.move_id, 'reconciled_payment_ids', False)
                    if payments:
                        for pay in payments:
                            sheet.write(row, 16, pay.name or '')
                            sheet.write(row, 17, str(pay.date) if pay.date else '')
                            sheet.write(row, 18, float(pay.amount))
                            row += 1
                    else:
                        row += 1

        workbook.close()
        output.seek(0)
        xlsx_bytes = output.getvalue()
        output.close()
        if response is not None and hasattr(response, 'stream') and hasattr(response.stream, 'write'):
            response.stream.write(xlsx_bytes)
        return xlsx_bytes
