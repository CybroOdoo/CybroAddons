# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sabeel B (odoo@cybrosys.com)
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
from datetime import datetime
from odoo import http, _
from odoo.http import request
from odoo.addons.website.controllers import main


class CustomerRegistration(main.Home):
    """Class to manage and create website return orders"""
    @http.route('/sale_return', type='json', methods=['POST'],
                auth="public", website=True,
                csrf=False)
    def sale_return(self, **kwargs):
        """Controller to create return order"""
        product_id = request.env['product.product'].sudo().search([
            ('id', '=', int(kwargs['product']))])
        order = request.env['sale.order'].sudo().search([
            ('id', '=', int(kwargs['order_id']))])
        values = {
            'partner_id': order.partner_id.id,
            'sale_order_id': order.id,
            'product_id': product_id.id,
            'quantity': kwargs['qty'],
            'reason': kwargs['reason'],
            'user_id': request.env.uid,
            'create_date': datetime.now(),
        }
        stock_picks = request.env['stock.picking'].search([
            ('origin', '=', order.name)])
        moves = (stock_picks.mapped('move_ids_without_package').filtered
                 (lambda p: p.product_id == product_id))
        if moves:
            moves = moves.sorted('product_uom_qty', reverse=True)
            values.update({'state': 'draft'})
            ret_order = request.env['sale.return'].create(values)
            ret_order.return_confirm()
            moves[0].picking_id.return_order_id = ret_order.id
            moves[0].picking_id.return_order_picking = False
        return True

    @http.route('/order_quantity', auth='public', type='json',
                website=True)
    def return_quantity(self, **kwargs):
        """Check the existing records for total returned quantity"""
        current_order = (request.env['sale.order'].sudo().browse
                         (int(kwargs['current_order'])))
        for rec in current_order.order_line.filtered(
                lambda ids: ids.product_id.id == int(
                    kwargs['product_id'])):
            return_order = request.env['sale.return'].sudo().search([
                ('sale_order_id', '=', current_order.id),
                ('product_id', '=', int(kwargs['product_id'])),
                ('state', 'in', ('confirm', 'done'))])
            if return_order:
                remaining_qty = rec.qty_delivered - sum(
                    return_order.mapped('quantity'))
                if remaining_qty == 0:
                    rec.return_qty = True
                return remaining_qty
            else:
                return rec.qty_delivered

    @http.route('/my/request-thank-you', website=True, page=True,
                auth='public', csrf=False)
    def maintenance_request_thanks(self):
        """Thank you page"""
        return (request.render
                ('website_return_management.customers_request_thank_page'))
