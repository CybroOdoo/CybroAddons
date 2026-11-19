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
from ast import literal_eval
from odoo import models


class Website(models.Model):
    """Extends the 'website' model to filter product search."""
    _inherit = "website"

    def _search_with_fuzzy(
        self, search_type, search, offset, limit, order, options
    ):
        """Extend base search functionality to include visibility filtering."""
        res = super()._search_with_fuzzy(
            search_type, search, offset, limit, order, options
        )
        response = list(res)
        user = self.env.user
        available_products = self.env['product.template']
        available_categ = self.env['product.public.category']
        mode = 'null'

        if not response[1]:
            return tuple(response)

        first_detail = response[1][0]
        if first_detail and first_detail.get('model') in (
            'product.template',
            'product.public.category',
        ):
            partner = user.partner_id
            if partner and partner.filter_mode != 'null':
                mode = partner.filter_mode
                if mode == 'product_only':
                    available_products = partner.website_available_product_ids
                elif mode == 'categ_only':
                    available_categ = partner.website_available_cat_ids
            elif user._is_public():
                params = self.env['ir.config_parameter'].sudo()
                guest_visibility = params.get_bool(
                    'is_product_visibility_guest_user'
                )
                if guest_visibility:
                    mode = params.get_str('filter_mode')
                    if mode == 'product_only':
                        products = literal_eval(
                            params.get_str(
                                'website_product_visibility.'
                                'available_products_for_guest_ids',
                                '[]',
                            )
                        )
                        available_products = self.env[
                            'product.template'
                        ].sudo().browse(products)
                    elif mode == 'categ_only':
                        cat = literal_eval(
                            params.get_str(
                                'website_product_visibility.'
                                'available_cat_for_guest_ids',
                                '[]',
                            )
                        )
                        available_categ = self.env[
                            'product.public.category'
                        ].sudo().browse(cat)
            elif user.has_group('base.group_portal'):
                params = self.env['ir.config_parameter'].sudo()
                portal_visibility = params.get_bool(
                    'is_product_visibility_portal_user'
                )
                if portal_visibility:
                    mode = params.get_str('filter_mode_portal')
                    if mode == 'product_only':
                        products = literal_eval(
                            params.get_str(
                                'website_product_visibility.'
                                'available_products_for_portal_ids',
                                '[]',
                            )
                        )
                        available_products = self.env[
                            'product.template'
                        ].sudo().browse(products)
                    elif mode == 'categ_only':
                        cat = literal_eval(
                            params.get_str(
                                'website_product_visibility.'
                                'available_cat_for_portal_ids',
                                '[]',
                            )
                        )
                        available_categ = self.env[
                            'product.public.category'
                        ].sudo().browse(cat)

            if mode == 'categ_only' and available_categ:
                available_categ = self.env[
                    'product.public.category'
                ].search([('id', 'child_of', available_categ.ids)])

            for detail in response[1]:
                if detail.get('results'):
                    if detail.get('model') == 'product.template':
                        if mode == 'product_only' and available_products:
                            detail['results'] &= available_products
                        elif mode == 'categ_only' and available_categ:
                            detail['results'] = detail['results'].filtered(
                                lambda p: any(
                                    c in available_categ
                                    for c in p.public_categ_ids
                                )
                            )
                    elif detail.get('model') == 'product.public.category':
                        if mode == 'categ_only' and available_categ:
                            detail['results'] &= available_categ
                        elif mode == 'product_only' and available_products:
                            detail['results'] &= (
                                available_products.mapped('public_categ_ids')
                            )
                detail['count'] = len(detail.get('results', []))

            response[0] = sum(
                d.get('count', 0) for d in response[1]
            )
        return tuple(response)

    def available_products(self):
        """Return available products for current user partner."""
        self.ensure_one()
        partner = self.env.user.sudo().partner_id
        return partner.website_available_product_ids
