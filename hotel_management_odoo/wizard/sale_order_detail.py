# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
################################################################################
import json
import io
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

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
                                           default=date_utils.json_default),
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
        room_booking = self.env['room.booking'].search_read(domain=domain,
                                                            fields=[
                                                                'partner_id',
                                                                'name',
                                                                'checkin_date',
                                                                'checkout_date',
                                                                'amount_total'])
        for rec in room_booking:
            rec['partner_id'] = rec['partner_id'][1]
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
        sheet.merge_range('A1:F1', 'Sale Order', head)
        sheet.set_column('A2:F2', 18)
        sheet.set_row(0, 30)
        sheet.set_row(1, 20)
        sheet.write('A2', 'Sl No.', cell_format)
        sheet.write('B2', 'Guest Name', cell_format)
        sheet.write('C2', 'Check In', cell_format)
        sheet.write('D2', 'Check Out', cell_format)
        sheet.write('E2', 'Reference No.', cell_format)
        sheet.write('F2', 'Total Amount', cell_format)
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
            row = row + 1
            value = value + 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
