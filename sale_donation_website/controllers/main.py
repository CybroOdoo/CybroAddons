# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleDelivery(WebsiteSale):

    @http.route(['/shop/update_donation'], type='json', auth='public',
                methods=['POST'], website=True, csrf=False)
    def update_eshop_donation(self, **post):
        order = request.website.sale_get_order()
        donation_id = request.env['donation.rule'].sudo().browse(int(post['donation_id']))
        donate_product = request.env.ref('sale_donation_website.product_product_view_create')

        if post.get('checked'):
            # Add the donation to M2M field
            order.write({'donation_ids': [(4, donation_id.id)]})
            # Add line if not already there
            donation_lines = order.order_line.filtered(
                lambda l: l.product_id == donate_product and l.name == donation_id.name)
            if not donation_lines:
                order.order_line.create({
                    'order_id': order.id,
                    'product_id': donate_product.id,
                    'name': donation_id.name,
                    'product_uom': donate_product.uom_id.id,
                    'product_uom_qty': 1,
                    'price_unit': donation_id.amount,
                    'is_donation': True,
                })
        else:
            # Remove the donation line
            order.order_line.filtered(
                lambda l: l.product_id == donate_product and l.name == donation_id.name and l.is_donation).unlink()
            # Also unlink from donation_ids M2M if needed
            order.write({'donation_ids': [(3, donation_id.id)]})

        return True
