# -*- coding: utf-8 -*-

import logging
from odoo import fields, http, tools, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class websale(WebsiteSale):

    @http.route(['/shop/buy_now'], type='http', auth="public", methods=['POST'], website=True)
    def pay(self, product_id_buy, add_qty=1):
        product_custom_attribute_values = None
        no_variant_attribute_values = None
        partner = request.website.env.user.partner_id
        pricelist_id = request.session.get('website_sale_current_pl') or request.website.get_current_pricelist().id
        pricelist = request.website.env['product.pricelist'].browse(pricelist_id).sudo()
        so_data = request.website._prepare_sale_order_values(partner, pricelist)
        sale_order = request.website.env['sale.order'].with_context(
            force_company=request.website.company_id.id).sudo().create(
            so_data)
        # set fiscal position
        if request.website.partner_id.id != partner.id:
            sale_order.onchange_partner_shipping_id()
        else:  # For public user, fiscal position based on geolocation
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1).id
                fp_id = request.env['account.fiscal.position'].sudo().with_context(force_company=request.website.company_id.id)._get_fpos_by_region(country_id)
                sale_order.fiscal_position_id = fp_id
            else:
                # if no geolocation, use the public user fp
                sale_order.onchange_partner_shipping_id()

        request.session['sale_order_id'] = sale_order.id
        sale_order.sudo()._cart_update(
            product_id=int(product_id_buy),
            add_qty=add_qty,
            set_qty=0,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values
        )
        # Take sale order id for payment confirmation page
        request.session['sale_last_order_id'] = sale_order.id
        return request.redirect("/shop/payment")
