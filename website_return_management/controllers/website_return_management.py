# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
################################################################################
from odoo.addons.website.controllers import main
from datetime import datetime
from odoo import http
from odoo.http import request


class CustomerRegistration(main.Home):

    @http.route('/sale_return', type='http', methods=['POST'], auth="public", website=True,
                csrf=False)
    def sale_return(self, **kwargs):
        """Controller to create return order"""
        product_id = request.env['product.product'].sudo().browse(int(kwargs['product']))
        order = request.env['sale.order'].sudo().browse(int(kwargs['order_id']))
        qty = kwargs['qty']
        reason = kwargs['reason']
        values = {
            'partner_id': order.partner_id.id,
            'sale_order': order.id,
            'product_id': product_id.id,
            'quantity': qty,
            'reason': reason,
            'user_id': request.env.uid,
            'create_date': datetime.now(),
        }
        stock_picks = request.env['stock.picking'].search([('origin', '=', order.name)])
        moves = stock_picks.mapped('move_ids_without_package').with_user(1).filtered(lambda p: p.product_id == product_id)
        if moves:
            moves = moves.sorted('product_uom_qty', reverse=True)
            values.update({'state': 'draft'})
            ret_order = request.env['sale.return'].with_user(1).create(values)
            moves[0].picking_id.return_order = ret_order.id
            moves[0].picking_id.return_order_picking = False
        return request.redirect('/my/request-thank-you')

    @http.route('/my/request-thank-you', website=True, page=True, auth='public', csrf=False)
    def maintenance_request_thanks(self):
        return request.render('website_return_management.customers_request_thank_page')
