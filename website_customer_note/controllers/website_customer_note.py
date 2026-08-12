# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import http
from odoo.http import request


class WebsiteSaleCustomerNote(http.Controller):
    """Handle website sale customer note requests."""

    @http.route(
        '/shop/save_customer_note',
        type='json',
        auth='public',
        website=True,
        csrf=False,
    )
    def save_customer_note(self, order_id=None, customer_note=None, **kwargs):
        """Save customer note to the sale order before payment."""
        if not order_id:
            return {'success': False, 'error': 'No order_id provided'}
        order = request.env['sale.order'].sudo().browse(int(order_id))
        if order.exists():
            order.write({'customer_note': (customer_note or '').strip()})
            return {'success': True}
        return {'success': False, 'error': 'Order not found'}
