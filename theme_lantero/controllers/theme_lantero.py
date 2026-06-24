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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class LanteroTrackOrder(http.Controller):
    """
    Controller for handling the 'Track Order' functionality in the Lantero theme.
    Provides routes for users to check the status of their orders.
    """
    @http.route(['/track-order'], type='http', auth="public", website=True)
    def track_order(self, order_number=None, email=None, **kw):
        """
        Renders the order tracking page and handles tracking search requests.
        Iterates through pickings related to the order matching the provided order number
        and email to calculate shipping/delivery progress and status steps.
        :param str order_number: The unique identifier/name of the sale order.
        :param str email: The email address associated with the order's partner.
        :param dict kw: Additional keyword arguments.
        :return: Rendered HTML of the 'theme_lantero.lantero_track_order_page' template.
        """
        values = {
            'searched': False,
            'order': None,
            'error': None,
            'progress': 0,
            'status_step': 0,
            'picking': None,
            'order_number': order_number,
            'email': email,
        }
        if order_number and email:
            values['searched'] = True
            # Search sale.order record cleanly
            order = request.env['sale.order'].sudo().search([
                ('name', '=ilike', order_number.strip()),
                ('partner_id.email', '=ilike', email.strip())
            ], limit=1)
            if order:
                values['order'] = order
                progress = 20
                status_step = 1 # Steps: 1 (Placed), 2 (Processing/Hand-crafted), 3 (Shipped), 4 (Out for delivery), 5 (Delivered)
                # Retrieve associated pickings/delivery orders (robust lookup)
                pickings = None
                if hasattr(order, 'picking_ids'):
                    pickings = order.picking_ids.filtered(lambda p: p.state != 'cancel')
                if pickings:
                    all_done = all(p.state == 'done' for p in pickings)
                    any_done = any(p.state == 'done' for p in pickings)
                    any_assigned = any(p.state == 'assigned' for p in pickings)
                    if all_done:
                        # Let's set Delivered if picking is completely completed
                        progress = 100
                        status_step = 5
                    elif any_done:
                        progress = 50
                        status_step = 3
                    elif any_assigned:
                        progress = 35
                        status_step = 2
                    else:
                        progress = 25
                        status_step = 2
                else:
                    if order.state in ('sale', 'done'):
                        progress = 35
                        status_step = 2
                values['progress'] = progress
                values['status_step'] = status_step
                if pickings:
                    values['picking'] = pickings[0]
            else:
                values['error'] = "We couldn't find an order matching that number and email. Please check your entries and try again."
        # Retrieve the website page record for robust website builder/editor support
        page = request.env['website.page'].sudo().search([
            ('url', '=', '/track-order'),
            ('website_id', 'in', (request.website.id, False))
        ], order='website_id', limit=1)
        if not page:
            page = request.env['website.page'].sudo().search([
                ('view_id.key', '=', 'theme_lantero.lantero_track_order_page'),
                ('website_id', 'in', (request.website.id, False))
            ], order='website_id', limit=1)
        if page:
            values['main_object'] = page
        return request.render('theme_lantero.lantero_track_order_page', values)
