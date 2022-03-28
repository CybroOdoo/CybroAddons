# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Shijin V (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo.addons.web.controllers import main
from datetime import datetime
from odoo import http
from odoo.http import request


class CustomerRegistration(main.Home):
    @http.route('/sale_return', type='json', csrf=False, auth="public", website=True)
    def sale_return(self, **kwargs, ):
        """Controller to create return order"""
        if kwargs.get('vals'):
            lines = []
            so_id = False
            for line in kwargs.get('vals'):
                so_id = request.env['sale.order'].sudo().search([('id', '=', int(line['order_id']))])
                qty = int(line['quantity'])
                d_qty = int(line['deli_qty'])
                reason = line['reason']
                if qty > 0:
                    lines.append((0, 0,{'product_id': line['product_id'],
                                  'received_qty': qty,
                                  'quantity': d_qty,
                                  'reason':reason
                                  }))
            if so_id:
                values = {
                    'partner_id': so_id.partner_id.id,
                    'sale_order': so_id.id,
                    'user_id': request.env.uid,
                    'create_date': datetime.now(),
                    'return_line_ids':lines
                }
                stock_picks = request.env['stock.picking'].sudo().search([('origin', '=', so_id.name)])
                moves = stock_picks.mapped('move_ids_without_package').sudo().filtered(
                            lambda p: p.product_id.id == line['product_id'])
                if moves:
                    moves = moves.sorted('product_uom_qty', reverse=True)
                    values.update({'state': 'draft'})
                    ret_order = request.env['sale.return'].sudo().create(values)
                    moves[0].picking_id.return_order = ret_order.id
                    moves[0].picking_id.return_order_picking = False
                return True
        return False

    @http.route('/my/request-thank-you', website=True, page=True, auth='public', csrf=False)
    def maintenance_request_thanks(self):
        return request.render('website_multi_product_return_management.customers_request_thank_page')