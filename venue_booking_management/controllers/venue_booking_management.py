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
from odoo import fields, http
from odoo.http.stream import content_disposition, request
from odoo.http.dispatcher import serialize_exception as _serialize_exception
from odoo.tools import html_escape


class XLSXReportController(http.Controller):
    """Controller Class for xlsx report"""

    @http.route('/venue_xlsx_reports', type='http', auth='user',
                methods=['POST', 'GET'])
    def get_report_xlsx(self, model, options, output_format, report_name, **kw):
        """Method for passing data to xlsx report"""
        uid = request.session.uid
        report_obj = request.env[model].with_user(uid)
        if isinstance(options, str):
            options = json.loads(options)
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                        ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                    ]
                )
                report_obj.get_xlsx_report(options, response)
                return response
            return request.not_found()
        except Exception as err:
            exception = _serialize_exception(err)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': exception
            }
            return request.make_response(html_escape(json.dumps(error)))



class VenueBookingController(http.Controller):
    """Class to add Venue booking menu in website"""

    @http.route('/venue/booking', type='http', auth='public', website=True)
    def venue_booking(self):
        """Function to render venue booking values to XML"""
        venue_ids = request.env['venue'].sudo().search([])
        state_ids = request.env['res.country.state'].sudo().search([])
        country_ids = request.env['res.country'].sudo().search([])
        return http.request.render(
            'venue_booking_management.venue_booking_page',
            {'venue_ids': venue_ids,
             'state_ids': state_ids,
             'country_ids': country_ids})

    @http.route('/booking/check_availability', type='json', auth='public', website=True)
    def check_availability(self, start_date=None, end_date=None, venue_id=None, **kwargs):
        """Check if venue is available for the given dates"""
        if not (start_date and end_date and venue_id):
            return {'available': False, 'message': 'Missing parameters'}
        overlapping = request.env['venue.booking'].sudo().search_count([
            ('start_date', '<', end_date),
            ('end_date', '>', start_date),
            ('venue_id', '=', int(venue_id)),
            ('state', 'in', ['confirm', 'invoice']),
        ])
        return {'available': overlapping == 0}

    @http.route('/booking/submit', type='http', auth='public', website=True)
    def booking_success_page(self, **post):

        """Function to create booking and return to success page"""
        if not request.env.user._is_public():
            partner_id = request.env.user.partner_id
            partner_vals = {}
            if post.get('mobile_no'):
                partner_vals['phone'] = post.get('mobile_no')
            if post.get('city'):
                partner_vals['city'] = post.get('city')
            if post.get('state'):
                partner_vals['state_id'] = int(post.get('state'))
            if post.get('country'):
                partner_vals['country_id'] = int(post.get('country'))
            if partner_vals:
                partner_id.sudo().write(partner_vals)
        else:
            partner_id = request.env['res.partner'].sudo().create({
                'name': post.get('name'),
                'phone': post.get('mobile_no'),
                'city': post.get('city'),
                'state_id': int(post.get('state')) if post.get('state') else False,
                'country_id': int(post.get('country')) if post.get('country') else False,
            })
        venue_id = request.env['venue'].browse(int(post.get('venue_type'))) if post.get('venue_type') else False
        values = {
            'partner_id': partner_id.id,
            'venue_id': venue_id.id if venue_id else False,
            'start_date': post.get('from_date'),
            'end_date': post.get('to_date'),
            'booking_type': post.get('booking_type'),
            'date': fields.Date.today()
        }
        booking_id = request.env['venue.booking'].sudo().create(values)
        return request.render(
            'venue_booking_management.venue_booking_success_page',
            {'partner_id': partner_id,
             'booking_id': booking_id})
