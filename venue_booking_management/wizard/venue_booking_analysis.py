# -*- coding: utf-8 -*-
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
import json
import io
import xlsxwriter
import pytz
from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools import json_default

class VenueBookingAnalysis(models.TransientModel):
    """Model for generating the Venue Booking Reports in xls and pdf"""
    _name = 'venue.booking.analysis'
    _description = 'Venue Booking Analysis'

    venue_id = fields.Many2one('venue',
                               help='You can choose the Venue')
    start_date = fields.Datetime(string="Start date",
                                 help='Venue Booking Start Date')
    end_date = fields.Datetime(string="End date", help='Venue Booking End Date')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help='Field to choosing the customer')
    def action_print_pdf(self):
        """Function used to print the PDF of the Venue Booking"""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(self.env._('Start Date must be less than End Date'))
        form_data = {
            'id': self.id,
            'venue_id': [self.venue_id.id, self.venue_id.name] if self.venue_id else False,
            'partner_id': [self.partner_id.id, self.partner_id.name] if self.partner_id else False,
            'start_date': str(self.start_date) if self.start_date else False,
            'end_date': str(self.end_date) if self.end_date else False,
        }
        data = {
            'model': 'venue.booking.analysis',
            'form': form_data,
        }
        return self.env.ref(
            'venue_booking_management.action_venue_booking_management_report').report_action(
            [], data=data)

    def action_print_xlsx(self):
        """Method of button for printing xlsx report"""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(self.env._('Start Date must be less than End Date'))
        rec = self.env.user.sudo().company_id
        user_tz = self.env.user.tz or 'UTC'
        current = fields.Datetime.now()
        current = pytz.UTC.localize(current).astimezone(pytz.timezone(user_tz))

        form_data = {
            'id': self.id,
            'venue_id': [self.venue_id.id, self.venue_id.name] if self.venue_id else False,
            'partner_id': [self.partner_id.id, self.partner_id.name] if self.partner_id else False,
            'start_date': str(self.start_date) if self.start_date else False,
            'end_date': str(self.end_date) if self.end_date else False,
        }
        
        data = {
            'today_date': current.strftime('%Y-%m-%d %H:%M:%S'),
            'company': [rec.partner_id.name or '', rec.street or '', ''],
            'form': form_data,
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {
                'model': 'venue.booking.analysis',
                'output_format': 'xlsx',
                'options': json.dumps(data, default=json_default),
                'report_name': 'Venue Booking Report',
            },
        }

    def get_xlsx_report(self, data, response):
        """Method for fetching data and printing xlsx report from controller"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Venue Booking Report')

        title_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'bold': True,
            'font_size': 16,
            'font_name': 'Calibri'
        })
        company_format = workbook.add_format({
            'font_size': 11,
            'font_name': 'Calibri'
        })
        label_bold = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'font_name': 'Calibri'
        })
        txt_head = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'border': 2,
            'font_name': 'Calibri',
            'align': 'left',
            'valign': 'vcenter'
        })
        txt_head_center = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'border': 2,
            'font_name': 'Calibri',
            'align': 'center',
            'valign': 'vcenter'
        })
        txt = workbook.add_format({
            'font_size': 10,
            'border': 1,
            'font_name': 'Calibri',
            'align': 'left',
            'valign': 'vcenter'
        })
        txt_center = workbook.add_format({
            'font_size': 10,
            'border': 1,
            'font_name': 'Calibri',
            'align': 'center',
            'valign': 'vcenter'
        })

        sheet.set_column('A:A', 8)
        sheet.set_column('B:B', 24)
        sheet.set_column('C:C', 26)
        sheet.set_column('D:D', 16)
        sheet.set_column('E:E', 24)
        sheet.set_column('F:F', 22)
        sheet.set_column('G:G', 22)
        sheet.set_column('H:H', 14)

        sheet.merge_range('D2:E2', 'Venue Booking Report', title_format)

        company_info = data.get('company', ['', '', ''])
        sheet.write(3, 0, company_info[0] if len(company_info) > 0 else '', company_format)
        sheet.write(4, 0, company_info[1] if len(company_info) > 1 else '', company_format)

        sheet.write(5, 0, 'Date:', label_bold)
        sheet.write(5, 1, data.get('today_date', ''), company_format)

        form_data = data.get('form', {})
        col_idx = 0
        if form_data.get('start_date'):
            sheet.write(7, 0, 'From:', label_bold)
            sheet.write(7, 1, str(form_data['start_date']), company_format)
            col_idx = 2
        if form_data.get('end_date'):
            sheet.write(7, col_idx, 'To:', label_bold)
            sheet.write(7, col_idx + 1, str(form_data['end_date']), company_format)
            col_idx += 2
        if form_data.get('partner_id'):
            partner_name = ''
            if isinstance(form_data['partner_id'], (list, tuple)):
                partner_name = form_data['partner_id'][1]
            sheet.write(7, col_idx, 'Customer:', label_bold)
            sheet.write(7, col_idx + 1, partner_name, company_format)

        headers = ['Sl.no', 'Ref No', 'Venue', 'Booking Type', 'Customer', 'Start Date', 'End Date', 'State']
        for col, h in enumerate(headers):
            if col == 0:
                sheet.write(9, col, h, txt_head_center)
            else:
                sheet.write(9, col, h, txt_head)

        where_clauses = ["1=1"]
        params = []
        if form_data.get("partner_id"):
            partner_val = form_data['partner_id'][0] if isinstance(form_data['partner_id'], (list, tuple)) else form_data['partner_id']
            where_clauses.append("tb.partner_id = %s")
            params.append(partner_val)
        if form_data.get("start_date"):
            where_clauses.append("tb.start_date >= %s")
            params.append(form_data['start_date'])
        if form_data.get("end_date"):
            where_clauses.append("tb.end_date <= %s")
            params.append(form_data['end_date'])
        if form_data.get("venue_id"):
            venue_val = form_data['venue_id'][0] if isinstance(form_data['venue_id'], (list, tuple)) else form_data['venue_id']
            where_clauses.append("tb.venue_id = %s")
            params.append(venue_val)

        where_str = " AND ".join(where_clauses)
        query = f"""
            SELECT tb.ref, pr.name, fv.name as venue, tb.booking_type,
                   tb.date, tb.start_date, tb.end_date, tb.state
            FROM venue_booking as tb
            INNER JOIN res_partner as pr ON pr.id = tb.partner_id
            INNER JOIN venue as fv ON fv.id = tb.venue_id
            WHERE {where_str}
            ORDER BY tb.id ASC
        """
        self.env.cr.execute(query, params)
        rec = self.env.cr.dictfetchall()

        row = 10
        for k, record in enumerate(rec, start=1):
            sheet.write(row, 0, k, txt_center)
            sheet.write(row, 1, record.get('ref') or '', txt)
            sheet.write(row, 2, record.get('venue') or '', txt)

            b_type = record.get('booking_type') or ''
            if b_type == 'day':
                b_type_str = 'Day'
            elif b_type == 'hour':
                b_type_str = 'Hours'
            else:
                b_type_str = str(b_type).capitalize()
            sheet.write(row, 3, b_type_str, txt)

            sheet.write(row, 4, record.get('name') or '', txt)

            start_dt = record.get('start_date')
            start_str = fields.Datetime.to_string(start_dt) if start_dt else ''
            sheet.write(row, 5, start_str, txt)

            end_dt = record.get('end_date')
            end_str = fields.Datetime.to_string(end_dt) if end_dt else ''
            sheet.write(row, 6, end_str, txt)

            st = record.get('state') or ''
            state_mapping = {
                'draft': 'Draft',
                'confirm': 'Confirm',
                'invoice': 'Invoiced',
                'close': 'closed',
                'cancel': 'Cancelled'
            }
            state_str = state_mapping.get(st, st.capitalize())
            sheet.write(row, 7, state_str, txt)

            row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

