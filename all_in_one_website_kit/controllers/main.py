# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers import main


class Home(main.Home):
    """The CustomerRegistration class is used for creating the sale return
        orders and displaying the thankyou page"""

    @http.route('/sale_return', type='http', methods=['POST'],
                auth="public", website=True, csrf=False)
    def sale_return(self, **kwargs):
        """Controller to create return order"""
        product_id = request.env['product.product'].sudo().browse(
            int(kwargs['product']))
        order = request.env['sale.order'].sudo().browse(int(kwargs['order_id']))
        values = {
            'partner_id': order.partner_id.id,
            'order_id': order.id,
            'product_id': product_id.id,
            'quantity': kwargs['qty'],
            'reason': kwargs['reason'],
            'user_id': request.env.uid,
            'create_date': datetime.now(),
        }
        stock_picks = request.env['stock.picking'].search(
            [('origin', '=', order.name)])
        moves = stock_picks.mapped('move_ids_without_package').filtered(
            lambda p: p.product_id == product_id)
        if moves:
            moves = moves.sorted('product_uom_qty', reverse=True)
            values.update({'state': 'draft'})
            ret_order = request.env['sale.return'].create(values)
            moves[0].picking_id.return_order_id = ret_order.id
            moves[0].picking_id.return_order_picking = False
        return request.redirect('/my/request-thank-you')

    @http.route('/my/request-thank-you', website=True, page=True,
                auth='public', csrf=False)
    def maintenance_request_thanks(self):
        """opening thankyou page"""
        return request.render(
            'all_in_one_website_kit.customers_request_thank_page')
