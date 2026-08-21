# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Henna Mehjabin(<https://www.cybrosys.com>)
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
##############################################################################
from odoo import http
from odoo.http import request


class SaleOrderCancel(http.Controller):
    """Controller to handle sale order cancellation."""

    @http.route(
        '/cancel/reason/edit',
        type='jsonrpc',
        auth='public',
        website=False,
        csrf=False,
        methods=['POST']
    )
    def cancel_sale_order(self, **post):
        """Update cancellation reason and cancel the sale order."""
        sale_order = request.env['sale.order'].sudo().browse(
            int(post.get('sale_order_id'))
        )

        sale_order.write({
            'is_cancel': True,
            'cancellation_reason': post.get('reason'),
        })

        sale_order.with_context(
            disable_cancel_warning=True
        ).action_cancel()

        return {
            'success': True,
            'sale_order_id': sale_order.id,
        }
