# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev K P (odoo@cybrosys.com)
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
################################################################################
from datetime import datetime
from odoo.addons.web.controllers import home
from odoo import http
from odoo.http import request


class CustomerRegistration(home.Home):
    """In this class, creating sale returns"""

    @http.route('/sale_return', type='json', csrf=False, auth="public",
                website=True)
    def sale_return(self, **kwargs, ):
        """Controller to create return order"""
        if kwargs.get('vals'):
            lines = []
            so_id = False
            for line in kwargs.get('vals'):
                so_id = request.env['sale.order'].sudo().search(
                    [('id', '=', int(line['order_id']))])
                qty = int(line['quantity'])
                d_qty = int(line['deli_qty'])
                reason = line['reason']
                if qty > 0:
                    lines.append((0, 0, {'product_id': line['product_id'],
                                         'received_qty': qty,
                                         'quantity': d_qty,
                                         'reason': reason
                                         }))
            if so_id:
                values = {
                    'partner_id': so_id.partner_id.id,
                    'sale_order_id': so_id.id,
                    'user_id': request.env.uid,
                    'create_date': datetime.now(),
                    'return_line_ids': lines
                }
                stock_picks = request.env['stock.picking'].sudo().search(
                    [('origin', '=', so_id.name)])
                moves = stock_picks.mapped(
                    'move_ids_without_package').sudo().filtered(
                    lambda p: p.product_id.id == line['product_id'])
                if moves:
                    moves = moves.sorted('product_uom_qty', reverse=True)
                    values.update({'state': 'draft'})
                    ret_order = request.env['sale.return'].sudo().create(values)
                    moves[0].picking_id.return_order_id = ret_order.id
                    moves[0].picking_id.return_order_picking = False
                return True
        return False

    @http.route('/my/request-thank-you', website=True, page=True,
                auth='public', csrf=False)
    def maintenance_request_thanks(self):
        """Controller to redirect to the success page when return order
         submitted successfully"""
        return request.render(
            'website_multi_product_return_management.'
            'customers_request_thank_page')
