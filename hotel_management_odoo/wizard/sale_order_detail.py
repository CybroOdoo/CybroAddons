# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ADARSH K (odoo@cybrosys.com)
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
###############################################################################
import io
import json
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import json_default

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class SaleOrderWizard(models.TransientModel):
    """Pdf Report for Sale Order"""
    _name = "sale.order.detail"
    _description = "Room Booking Details"

    checkin = fields.Date(help="Choose the Checkin Date", string="Check In")
    checkout = fields.Date(help="Choose the Checkout Date", string="Check Out")
    filter_draft = fields.Boolean(help="Include bookings in Draft state",
                                  string="Draft")
    filter_reserved = fields.Boolean(
        help="Include bookings in Reserved state", string="Reserved")
    filter_check_in = fields.Boolean(
        help="Include bookings in Check In state", string="Check In")
    filter_check_out = fields.Boolean(
        help="Include bookings in Check Out state", string="Check Out")
    filter_cancel = fields.Boolean(
        help="Include bookings in Cancelled state", string="Cancelled")
    filter_done = fields.Boolean(help="Include bookings in Done state",
                                 string="Done")

    def action_sale_order_pdf(self):
        """Button action for creating Sale Order Pdf Report"""
        data = {
            'booking': self.generate_data(),
        }
        return self.env.ref(
            'hotel_management_odoo.action_report_sale_order').report_action(
            self, data=data)

    def action_sale_order_excel(self):
        """Button action for creating Sale Order Report"""
        data = {
            'booking': self.generate_data(),
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'sale.order.detail',
                     'options': json.dumps(data,
                                           default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def generate_data(self):
        """Generate data to be printed in the report"""
        domain = []
        if self.checkin and self.checkout:
            if self.checkin > self.checkout:
                raise ValidationError(_(
                    'Check-in date should be less than Check-out date'))
        if self.checkin:
            domain.append(('checkin_date', '>=', self.checkin), )
        if self.checkout:
            domain.append(('checkout_date', '<=', self.checkout), )
        state_map = {
            'filter_draft': 'draft',
            'filter_reserved': 'reserved',
            'filter_check_in': 'check_in',
            'filter_check_out': 'check_out',
            'filter_cancel': 'cancel',
            'filter_done': 'done',
        }
        states = [state for field_name, state in state_map.items() if
                  self[field_name]]
        if states:
            domain.append(('state', 'in', states))
        room_booking = self.env['room.booking'].search_read(domain=domain,
                                                            fields=[
                                                                'partner_id',
                                                                'name',
                                                                'checkin_date',
                                                                'checkout_date',
                                                                'amount_total',
                                                                'state'])
        state_selection = dict(
            self.env['room.booking']._fields['state'].selection)
        for rec in room_booking:
            rec['partner_id'] = rec['partner_id'][1]
            rec['state'] = state_selection.get(rec['state'], rec['state'])
        return room_booking

    def get_xlsx_report(self, data, response):
        """Organizing xlsx report"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format(
            {'font_size': '14px', 'bold': True, 'align': 'center',
             'border': True})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '23px',
             'border': True})
        body = workbook.add_format(
            {'align': 'left', 'text_wrap': True, 'border': True})
        sheet.merge_range('A1:G1', 'Sale Order', head)
        sheet.set_column('A2:G2', 18)
        sheet.set_row(0, 30)
        sheet.set_row(1, 20)
        sheet.write('A2', 'Sl No.', cell_format)
        sheet.write('B2', 'Guest Name', cell_format)
        sheet.write('C2', 'Check In', cell_format)
        sheet.write('D2', 'Check Out', cell_format)
        sheet.write('E2', 'Reference No.', cell_format)
        sheet.write('F2', 'Total Amount', cell_format)
        sheet.write('G2', 'State', cell_format)
        row = 2
        column = 0
        value = 1
        for i in data['booking']:
            sheet.write(row, column, value, body)
            sheet.write(row, column + 1, i['partner_id'], body)
            sheet.write(row, column + 2, i['checkin_date'], body)
            sheet.write(row, column + 3, i['checkout_date'], body)
            sheet.write(row, column + 4, i['name'], body)
            sheet.write(row, column + 5, "{:.2f}".format(i['amount_total']),
                        body)
            sheet.write(row, column + 6, i['state'], body)
            row = row + 1
            value = value + 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
