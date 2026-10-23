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
import hmac

from odoo import http
from odoo.http import request


class Tracking(http.Controller):
    """Controller for the website delivery tracking page."""

    @http.route('/tracking/details', type='http', auth="user", website=True,
                csrf=False)
    def get_track_details(self):
        """Render the delivery tracking page."""
        return request.render(
            'website_order_delivery_tracking.tracking_template')

    @http.route(['/tracking/details/update'], type='jsonrpc', auth="user")
    def input_data_processing(self, **post):
        """Return the delivery details for the given tracking reference."""
        tracking_ref = post.get('input_data')
        if not tracking_ref:
            return []
        track_data = request.env['stock.picking'].sudo().search(
            [('carrier_tracking_ref', '=', tracking_ref)])
        default_status = request.env._("Status currently not available")
        return [
            [
                rec.name,
                rec.origin or '',
                rec.carrier_id.name or '',
                rec.tracking_status or default_status,
            ]
            for rec in track_data
        ]

    @http.route('/tracking/details/edit', type='jsonrpc', auth="public",
                website=False, csrf=False, methods=['POST'])
    def track_data_edit(self, **post):
        """Update the tracking status of the delivery, if the API key is
        correct."""
        tracking_number = post.get('tracking_number')
        api_key = post.get('api_key')
        tracking_api = request.env['ir.config_parameter'].sudo().get_str(
            'website_order_delivery_tracking.delivery_tracking_api_key')
        if not (tracking_number and api_key and tracking_api):
            return []
        if not hmac.compare_digest(str(api_key).encode(),
                                   tracking_api.encode()):
            return []
        track_data = request.env['stock.picking'].sudo().search(
            [('carrier_tracking_ref', '=', tracking_number)])
        if not track_data:
            return []
        track_data.write({'tracking_status': post.get('tracking_status')})
        return track_data[:1].tracking_status
