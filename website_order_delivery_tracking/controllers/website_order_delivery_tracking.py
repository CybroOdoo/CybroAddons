# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request


class Tracking(http.Controller):
    """Class representing Tracking"""

    @http.route('/tracking/details', type='http', auth="user", website=True,
                csrf=False)
    def get_track_details(self):
        """Track data"""
        return request.render(
            'website_order_delivery_tracking.trackingTemplate')

    @http.route(['/tracking/details/update'], type='json', auth="user",
                website=True)
    def input_data_processing(self, **post):
        """Fetch input json data sent from js"""
        track_data = request.env['stock.picking'].search(
            [('carrier_tracking_ref', '=', post.get('input_data'))])
        tracking_details = [
            [
                rec.name,
                rec.origin,
                rec.carrier_id.name,
                rec.tracking_status or 'Status currently not available',
            ]
            for rec in track_data
        ]
        return tracking_details

    @http.route('/tracking/details/edit', type='json', auth="public",
                website=False,
                csrf=False, methods=['GET', 'POST'])
    def track_data_edit(self, **post):
        """Edit tracking data"""
        tracking_api = request.env['ir.config_parameter'].sudo().get_param(
            'stock.delivery_tracking_api_key')
        track_data = request.env['stock.picking'].sudo().search(
            [('carrier_tracking_ref', '=', post.get('tracking_number'))])
        if track_data and post.get(
                'api_key') == tracking_api:
            track_data.write({
                'tracking_status': post.get('tracking_status'),
            })
            return track_data.tracking_status
        else:
            return []
