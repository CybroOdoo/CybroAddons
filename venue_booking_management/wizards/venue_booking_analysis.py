# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Risvana AR (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import json
import pytz
from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools import date_utils, io, xlsxwriter


class VenueBookingAnalysis(models.TransientModel):
    """Model for generating the Venue Booking Reports in xls and pdf"""
    _name = 'venue.booking.analysis'
    _description = 'Venue Booking Analysis'

    venue_id = fields.Many2one('venue', string='Venue',
                               help='You can choose the Venue')
    start_date = fields.Datetime(string="Start date", help='Venue Booking Start Date')
    end_date = fields.Datetime(string="End date", help='Venue Booking End Date')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help='Field to choosing the customer')

    def action_print_pdf(self):
        """Function used to print the PDF of the Venue Booking"""
        venue = self.env['venue.booking'].search([])
        data = {
            'model': 'venue.booking.analysis',
            'form': self.read()[0],
            'venue': venue
            }
        return self.env.ref(
            'venue_booking_management.action_venue_booking_management_report').report_action(
            self, data=data)

    def action_print_xlsx(self):
        """Method of button for printing xlsx report"""
        rec = self.env.user.sudo().company_id
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')
        user_tz = self.env.user.tz
        current = fields.datetime.now()
        current = pytz.UTC.localize(current)
        current = current.astimezone(pytz.timezone(user_tz))
        venue = self.env['venue.booking'].search([])
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'customer': self.partner_id.id,
            'venue_id': self.venue_id,
            'today_date': current,
            'company': [rec.partner_id.name, rec.street, rec.favicon],
            'form': self.read()[0],
            'venue': venue
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'venue.booking.analysis',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Venue Booking Report', },
        }

    def get_xlsx_report(self, data, response):
        """Method for fetching data and printing xlsx report from controller"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center',
                                    'bold': True, 'font_size': '20px'})
        cell_head_format = workbook.add_format({'font_size': '12px'})
        cell_data_format = workbook.add_format({'font_size': '10px'})
        txt_head = workbook.add_format({'bold': True, 'font_size': '12px', 'border': 2})
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        sheet.merge_range('F2:M3', 'Venue Booking Report', head)
        sheet.merge_range('B4:E4', data['company'][0], cell_head_format)
        sheet.merge_range('B5:E5', data['company'][1], cell_head_format)
        sheet.write('B6', 'Date:', cell_head_format)
        sheet.merge_range('C6:E6', data['today_date'], cell_data_format)
        form_data = data['form']
        if form_data['start_date'] and form_data['end_date'] and form_data['partner_id']:
            customer_name = self.env['res.partner'].browse(int(
                form_data['partner_id'][0])).name
            sheet.write('B8', 'From:', cell_head_format)
            sheet.merge_range('C8:D8', form_data['start_date'], cell_data_format)
            sheet.write('F8', 'To:', cell_head_format)
            sheet.merge_range('G8:H8', form_data['end_date'], cell_data_format)
            sheet.merge_range('J8:K8', 'Customer:', cell_head_format)
            sheet.merge_range('L8:N8', customer_name, cell_data_format)
        elif form_data['start_date'] and form_data['end_date']:
            sheet.write('B8', 'From:', cell_head_format)
            sheet.merge_range('C8:D8', form_data['start_date'],
                              cell_data_format)
            sheet.write('F8', 'To:', cell_head_format)
            sheet.merge_range('G8:H8', form_data['end_date'], cell_data_format)
        elif form_data['start_date'] and form_data['partner_id']:
            customer_name = self.env['res.partner'].browse(int(
                form_data['partner_id'][0])).name
            sheet.write('B8', 'From:', cell_head_format)
            sheet.merge_range('C8:D8', form_data['start_date'], cell_data_format)
            sheet.merge_range('F8:G8', 'Customer:', cell_head_format)
            sheet.merge_range('H8:J8', customer_name, cell_data_format)
        elif form_data['partner_id'] and form_data['end_date']:
            customer_name = self.env['res.partner'].browse(int(
                form_data['partner_id'][0])).name
            sheet.write('B8', 'To:', cell_head_format)
            sheet.merge_range('C8:D8', form_data['end_date'], cell_data_format)
            sheet.merge_range('F8:G8', 'Customer:', cell_head_format)
            sheet.merge_range('H8:J8', customer_name, cell_data_format)
        elif form_data['start_date']:
            sheet.write('B8', 'From:', cell_head_format)
            sheet.merge_range('C8:D8', form_data['start_date'], cell_data_format)
        elif form_data['end_date']:
            sheet.write('B8', 'To:', cell_head_format)
            sheet.merge_range('C8:D8', form_data['end_date'], cell_data_format)
        elif form_data['partner_id']:
            customer_name = self.env['res.partner'].browse(int(
                form_data['partner_id'][0])).name
            sheet.merge_range('B8:C8', 'Customer:', cell_head_format)
            sheet.merge_range('D8:E8', customer_name, cell_data_format)
        sheet.write(10, 0, 'Sl.no', txt_head)
        sheet.merge_range('B11:D11', 'Ref No', txt_head)
        sheet.merge_range('E11:G11', 'Venue', txt_head)
        sheet.merge_range('H11:I11', 'Booking Type', txt_head)
        sheet.merge_range('J11:L11', 'Customer', txt_head)
        sheet.merge_range('M11:N11', 'Start Date', txt_head)
        sheet.merge_range('O11:P11', 'End Date', txt_head)
        sheet.merge_range('Q11:R11', 'State', txt_head)
        where = '1=1'
        if form_data["partner_id"]:
            where += """ AND tb.partner_id = %s""" % form_data['partner_id'][0]
        if form_data['start_date']:
            where += """ AND tb.date >= '%s'""" % form_data['start_date']
        if form_data['end_date']:
            where += """ AND tb.date <= '%s'""" % form_data['end_date']
        if form_data['venue_id']:
            where += """ AND tb.venue_id = %s""" % form_data['venue_id'][0]
        self.env.cr.execute("""
                    SELECT tb.ref, pr.name, fv.name as venue, tb.booking_type,
                    tb.date, tb.start_date, tb.end_date, tb.state
                    FROM venue_booking as tb
                    INNER JOIN res_partner as pr ON pr.id = tb.partner_id
                    INNER JOIN venue as fv ON fv.id = tb.venue_id
                    WHERE %s
                """ % where)
        rec = self.env.cr.dictfetchall()
        j = 11
        k = 1
        for i in range(0, len(rec)):
            sheet.write(j, 0, k, txt)
            sheet.merge_range('B%d:D%d' % (j + 1, j + 1), rec[i]['ref'], txt)
            sheet.merge_range('E%d:G%d' % (j + 1, j + 1), rec[i]['venue'], txt)
            if rec[i]['booking_type'] == 'day':
                sheet.merge_range('H%d:I%d' % (j + 1, j + 1), 'Day', txt)
            elif rec[i]['booking_type'] == 'hour':
                sheet.merge_range('H%d:I%d' % (j + 1, j + 1), 'Hour', txt)
            else:
                sheet.merge_range('H%d:I%d' % (j + 1, j + 1), rec[i]['booking_type'] , txt)
            sheet.merge_range('J%d:L%d' % (j + 1, j + 1), rec[i]['name'], txt)
            sheet.merge_range('M%d:N%d' % (j + 1, j + 1),
                              fields.Datetime.to_string(rec[i]['start_date']), txt)
            sheet.merge_range('O%d:P%d' % (j + 1, j + 1),
                              fields.Datetime.to_string(rec[i]['end_date']), txt)
            if rec[i]['state'] == 'draft':
                sheet.merge_range('Q%d:R%d' % (j + 1, j + 1), 'Draft', txt)
            elif rec[i]['state'] == 'invoice':
                sheet.merge_range('Q%d:R%d' % (j + 1, j + 1), 'Invoiced', txt)
            elif rec[i]['state'] == 'confirm':
                sheet.merge_range('Q%d:R%d' % (j + 1, j + 1), 'Confirm', txt)
            elif rec[i]['state'] == 'cancel':
                sheet.merge_range('Q%d:R%d' % (j + 1, j + 1), 'Cancelled', txt)
            elif    rec[i]['state'] == 'close':
                sheet.merge_range('Q%d:R%d' % (j + 1, j + 1), 'closed', txt)
            else:
                sheet.merge_range('Q%d:R%d' % (j + 1, j + 1), rec[i]['state'], txt)
            j += 1
            k += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
