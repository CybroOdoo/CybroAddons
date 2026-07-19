# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from ast import literal_eval
from odoo import models
from odoo.http import request


class Website(models.Model):
    """Extends the 'website' model to filter product search."""
    _inherit = "website"

    def _search_with_fuzzy(self, search_type, search, limit, order, options):
        """This method extends the base search functionality to include
         additional filtering"""
        res = super()._search_with_fuzzy(
            search_type, search, limit, order, options)
        response = list(res)
        user = request.env.user
        available_products = request.env['product.template']
        available_categ = request.env['product.public.category']
        mode = 'null'
        if not response[1]:
            return tuple(response)

        if response[1][0] and (response[1][0].get(
                'model', '') == 'product.template' or response[1][0].get(
            'model', '') == 'product.public.category'):
            partner = user.partner_id
            if partner.filter_mode != 'null':
                mode = partner.filter_mode
                if mode == 'product_only':
                    available_products = partner.website_available_product_ids
                elif mode == 'categ_only':
                    available_categ = partner.website_available_cat_ids
            elif user._is_public():
                guest_visibility = request.env['ir.config_parameter'].sudo().get_param(
                    'is_product_visibility_guest_user')
                if guest_visibility:
                    mode = request.env['ir.config_parameter'].sudo().get_param(
                        'filter_mode')
                    if mode == 'product_only':
                        products = literal_eval(
                            request.env['ir.config_parameter'].sudo().get_param(
                                'website_product_visibility.'
                                'available_products_for_guest_ids', '[]'))
                        available_products = request.env[
                            'product.template'].sudo().browse(products)
                    elif mode == 'categ_only':
                        cat = literal_eval(
                            request.env['ir.config_parameter'].sudo().get_param(
                                'website_product_'
                                'visibility.available_cat_for_guest_ids',
                                '[]'))
                        available_categ = request.env[
                            'product.public.category'].sudo().browse(cat)
            elif user.has_group('base.group_portal'):
                portal_visibility = request.env[
                    'ir.config_parameter'].sudo().get_param(
                    'product_visibility_portal_user')
                if portal_visibility:
                    mode = request.env['ir.config_parameter'].sudo().get_param(
                        'filter_mode_portal')
                    if mode == 'product_only':
                        products = literal_eval(
                            request.env['ir.config_parameter'].sudo().get_param(
                                'website_product_visibility.'
                                'available_products_for_portal_ids', '[]'))
                        available_products = request.env[
                            'product.template'].sudo().browse(products)
                    elif mode == 'categ_only':
                        cat = literal_eval(
                            request.env['ir.config_parameter'].sudo().get_param(
                                'website_product_visibility.available_cat_'
                                'for_portal_ids',
                                '[]'))
                        available_categ = request.env[
                            'product.public.category'].sudo().browse(cat)

            for detail in response[1]:
                if detail.get('results'):
                    if detail.get('model') == 'product.template':
                        if mode == 'product_only' and available_products:
                            detail['results'] &= available_products
                        elif mode == 'categ_only' and available_categ:
                            detail['results'] = detail['results'].filtered(
                                lambda p: any(
                                    c in available_categ for c in
                                    p.public_categ_ids))
                    elif detail.get(
                            'model') == 'product.public.category' and \
                            available_categ:
                        detail['results'] &= available_categ
        return tuple(response)

    def available_products(self):
        """Returns the available product (product.template) recordset for the current user's partner"""
        partner = request.env.user.sudo().partner_id
        return partner.website_available_product_ids
