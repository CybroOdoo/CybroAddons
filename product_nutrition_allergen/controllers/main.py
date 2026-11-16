# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import http
from odoo.http import Controller, request


class WebsiteSaleController(Controller):
    def _parse_product_id(self, name):
        if not name:
            return None
        try:
            clean_name = str(name).split('#')[0].split('?')[0].rstrip('/')
            product_info = clean_name.split('-')[-1]
            return int(product_info)
        except (ValueError, TypeError, IndexError):
            return None

    @http.route(['/shop/product_nutrition_details'],
                type='jsonrpc', auth="public")
    def product_nutrition_details(self, name):
        """ Return product nutrition details to js"""
        product_id = self._parse_product_id(name)
        if not product_id:
            return []
        lang = request.env['res.users'].browse(request.env.uid).lang
        product = request.env['product.template'].browse(product_id)
        if not product.exists():
            return []
        query = (""" select product_nutrition.name AS name,
                    product_nutrition.nutrition_value,uom_uom.name->> '{}' as 
                    uom_name from product_template join product_nutrition on 
                    product_template.id = product_nutrition.product_template_id 
                    join uom_uom on uom_uom.id = product_nutrition.uom_id """
                 .format(lang))
        if product.sudo().nutrition_ids:
            request.env.cr.execute(
                """{} where product_template.id ='{}'""".format(
                    query, product_id))
            conf = request.env.cr.dictfetchall()
            return conf
        return []

    @http.route(['/shop/product_ingredients_details'],
                type='jsonrpc', auth="public")
    def product_ingredients_details(self, name):
        """ Return product ingredient details to js"""
        product_id = self._parse_product_id(name)
        if not product_id:
            return ""
        product = request.env['product.template'].browse(product_id)
        if not product.exists():
            return ""
        return product.sudo().ingredients_information or ""

    @http.route(['/shop/product_allergy_details'],
                type='jsonrpc', auth="public")
    def product_allergy_details(self, name):
        """ Return product allergy details to js"""
        product_id = self._parse_product_id(name)
        if not product_id:
            return ""
        product = request.env['product.template'].browse(product_id)
        if not product.exists():
            return ""
        return product.sudo().allergy_information or ""
