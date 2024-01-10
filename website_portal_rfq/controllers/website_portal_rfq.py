# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal


class CustomerPortal(portal.CustomerPortal):
    """Helps to manage the customer portal controller"""

    def _prepare_home_portal_values(self, counters):
        """Update count of document to None"""
        values = super()._prepare_home_portal_values(counters)
        if 'qtn_count' in counters:
            values['qtn_count'] = None
        return values

    @http.route(
        ['/my/quotation_request', '/my/quotation_request/page/<int:page>'],
        type='http', auth="user",
        website=True)
    def portal_my_mo(self):
        """Returns quotation template with values."""
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'rfq_p',
            'login_partner': request.env.user.partner_id,
            'partners': request.env['res.partner'].search([]),
            'default_url': '/my/quotation_request',
        })
        return request.render(
            "website_portal_rfq.portal_my_rfq_requests",
            values)

    @http.route(['/my/send_request'], type="http", auth="public", website=True)
    def button_send_request(self, **kw):
        """Create a new quotation by submitting the request from the portal"""
        login_partner = request.env.user.partner_id
        partner_address = request.env['res.partner'].browse(
            [int(kw.get('address1', 0)), int(kw.get('address2', 0))])
        price_list = login_partner.property_product_pricelist
        order_lines = [(0, 0, {
            'product_id': product.id,
            'product_template_id': product.product_tmpl_id.id,
            'product_uom': request.env['uom.uom'].sudo().browse(
                int(kw.get('uom_' + key.split('_')[1]))).id,
            'price_unit': price_list._get_product_price(product, float(kw.get(
                'quantity_' + key.split('_')[
                    1]))) if price_list else product.list_price,
            'product_uom_qty': kw.get('quantity_' + key.split('_')[1]),
        }) for key, value in kw.items() if key.startswith('product_') for
                       product in
                       [request.env['product.product'].sudo().browse(
                           int(value))]]
        if len(partner_address) == 2 and order_lines:
            sale_order = request.env['sale.order'].sudo().create({
                'partner_id': login_partner.id,
                'partner_invoice_id': partner_address[0].id,
                'partner_shipping_id': partner_address[1].id,
                'note': kw.get('description'),
                'order_line': order_lines,
                'pricelist_id': price_list.id if price_list else False,
            })
            if sale_order:
                return request.render('quotation.thanks',
                                      {'sale_order': sale_order.name})
        return request.redirect('/my/quotation_request')

    @http.route(
        ['/my/product_details'],
        type='json', auth="user",
        website=True)
    def portal_product(self):
        """When add new product from portal the function will return the
         selected product from product.product"""
        products = request.env['product.product'].sudo().search(
            [('sale_ok', '=', True)])
        return {'product_id': [[product.display_name, product.id] for product in
                               products]}

    @http.route('/my/product_uom', type='json', auth="public", methods=['POST'],
                website=True)
    def get_product_uom(self, product_id=None, **kw):
        """Get Unit of measures based on the product"""
        if product_id:
            product = request.env['product.product'].sudo().browse(
                int(product_id))
            if product:
                uom_options = [(uom.id, uom.name) for uom in
                               product.uom_id.category_id.uom_ids]
                return {
                    'uom_ids': uom_options,
                }

    @http.route(
        ['/my/product_image'],
        type='json', auth="user",
        website=True, csrf=False)
    def portal_product_image(self, **kw):
        """When onchange the product, it will call this function to get
        the image of the product"""
        if kw.get('onchange_product_id'):
            return request.env['product.product'].sudo().browse(
                int(kw.get('onchange_product_id'))).image_1920
