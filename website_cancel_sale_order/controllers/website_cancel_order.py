# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
##############################################################################
from odoo import http
from odoo.http import request


class SaleOrderCancel(http.Controller):
    """Controller to handle the cancellation of a sales order.
    This controller provides an API endpoint to update the cancellation reason
    and state of a sale order to 'cancel'. The controller is accessible through
    a JSON API."""

    @http.route('/cancel/reason/edit', type='json', auth="public",
                website=False, csrf=False, methods=['GET', 'POST'])
    def cancel_sale_order(self, **post):
        """Update the cancellation reason and state of a sale order to
          'cancel'."""
        sale_order_id = request.env['sale.order'].sudo().browse(
            int(post.get('sale_order_id')))
        sale_order_id.is_cancel = True
        sale_order_id.cancellation_reason = post.get('reason')
        sale_order_id.with_context(disable_cancel_warning=True).action_cancel()
        return sale_order_id
