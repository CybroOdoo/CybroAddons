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
from odoo import fields,http
from odoo.http import content_disposition, request
from odoo.http import serialize_exception as _serialize_exception
from odoo.tools import html_escape


class XLSXReportController(http.Controller):
    """Controller Class for xlsx report"""
    @http.route('/venue_xlsx_reports', type='http', auth='user', methods=['POST'],
                csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_name):
        """Method for passing data to xlsx report"""
        uid = request.session.uid
        report_obj = request.env[model].with_user(uid)
        options = json.loads(options)
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[('Content-Type', 'application/vnd.ms-excel'), (
                        'Content-Disposition',
                        content_disposition(report_name + '.xlsx'))])
                report_obj.get_xlsx_report(options, response)
            return response
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
        return http.request.render('venue_booking_management.venue_booking_page',
                                   {'venue_ids': venue_ids,
                                    'state_ids': state_ids,
                                    'country_ids': country_ids})

    @http.route('/booking/submit', type='http', auth='public', website=True)
    def booking_success_page(self, **post):
        """Function to create booking and return to success page"""
        partner_id = request.env['res.partner'].sudo().create({
            'name': post.get('name'),
            'mobile': post.get('mobile_no'),
            'city': post.get('city'),
            'state_id': post.get('state'),
            'country_id': post.get('country')
        })
        venue_id = request.env['venue'].browse(int(post.get('venue_type')))
        values = {
            'partner_id': partner_id.id,
            'venue_id': venue_id.id,
            'start_date': post.get('from_date'),
            'end_date': post.get('to_date'),
            'booking_type': post.get('booking_type'),
            'date': fields.Date.today()
        }
        booking_id = request.env['venue.booking'].sudo().create(values)
        return request.render('venue_booking_management.venue_booking_success_page',
                              {'partner_id': partner_id,
                               'booking_id': booking_id})
