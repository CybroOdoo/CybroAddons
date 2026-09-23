# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Syamili K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################from odoo import http
from odoo import http
from odoo.http import Controller, request


class WebsiteSaleController(Controller):
    @http.route(['/shop/product_nutrition_details'],
                type='jsonrpc', auth="public")
    def product_nutrition_details(self, name):
        """ Return product nutrition details to js"""
        lang = request.env['res.users'].browse(request.env.uid).lang
        product_name = name.split('#')[0].split('-')
        product_info = product_name[len(product_name) - 1]
        product_id = product_info.split('?')[0]
        product = request.env['product.template'].sudo().browse(int(product_id))
        result = []
        for nutrition in product.nutrition_ids:
            result.append({
                'name': nutrition.name,
                'nutrition_value': nutrition.nutrition_value,
                'uom_name': nutrition.uom_id.name if nutrition.uom_id else '',
            })
        return result

    @http.route(['/shop/product_ingredients_details'],
                type='jsonrpc', auth="public")
    def product_ingredients_details(self, name):
        """ Return product ingredient details to js"""
        product_name = name.split('#')[0].split('-')
        product_info = product_name[len(product_name) - 1]
        product_id = product_info.split('?')[0]
        product = request.env['product.template'].browse(int(product_id))
        return product.sudo().ingredients_information

    @http.route(['/shop/product_allergy_details'],
                type='jsonrpc', auth="public")
    def product_allergy_details(self, name):
        """ Return product allergy details to js"""
        product_name = name.split('#')[0].split('-')
        product_info = product_name[len(product_name) - 1]
        product_id = product_info.split('?')[0]
        product = request.env['product.template'].browse(int(product_id))
        return product.sudo().allergy_information
