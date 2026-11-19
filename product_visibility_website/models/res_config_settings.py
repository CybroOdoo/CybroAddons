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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit 'res.config.settings' for website product visibility."""
    _inherit = 'res.config.settings'

    is_product_visibility_guest_user = fields.Boolean(
        string="Product Visibility Guest User",
        help="Enable product visibility rules for guest users.",
    )
    filter_mode = fields.Selection(
        [
            ('product_only', 'Product Wise'),
            ('categ_only', 'Category Wise'),
        ],
        string='Filter Mode',
        default='product_only',
        help="Filter mode of product visibility for guest users.",
    )
    available_products_for_guest_ids = fields.Many2many(
        'product.template',
        string='Available Products',
        domain="[('is_published', '=', True)]",
        help="The website will only display products which are selected. "
             "If no product is specified, all available products will be shown.",
    )
    available_cat_for_guest_ids = fields.Many2many(
        'product.public.category',
        string='Available Product Categories',
        help="The website will only display products which are within one of "
             "the selected category trees. If no category is specified, all "
             "available products will be shown.",
    )
    is_product_visibility_portal_user = fields.Boolean(
        string="Product Visibility Portal User",
        help="Enable product visibility rules for portal users.",
    )
    filter_mode_portal = fields.Selection(
        [
            ('product_only', 'Product Wise'),
            ('categ_only', 'Category Wise'),
        ],
        string='Filter Mode Portal',
        default='product_only',
        help="Filter mode of product visibility for portal users.",
    )
    available_products_for_portal_ids = fields.Many2many(
        'product.template',
        relation="available_product_for_portal_rel",
        string='Available Products for Portal',
        domain="[('is_published', '=', True)]",
        help="The website will only display products which are selected. "
             "If no product is specified, all available products will be shown.",
    )
    available_cat_for_portal_ids = fields.Many2many(
        'product.public.category',
        relation="available_cat_for_portal_rel",
        string='Available Portal Product Categories',
        help="The website will only display products which are within one of "
             "the selected category trees. If no category is specified, all "
             "available products will be shown.",
    )

    def set_values(self):
        """Set configuration parameters based on settings values."""
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        for record in self:
            params.set_bool(
                'is_product_visibility_guest_user',
                record.is_product_visibility_guest_user,
            )
            params.set_bool(
                'is_product_visibility_portal_user',
                record.is_product_visibility_portal_user,
            )
            params.set_str('filter_mode', record.filter_mode or 'product_only')
            params.set_str(
                'filter_mode_portal', record.filter_mode_portal or 'product_only'
            )

            guest_prods = record.available_products_for_guest_ids
            guest_cats = record.available_cat_for_guest_ids
            portal_prods = record.available_products_for_portal_ids
            portal_cats = record.available_cat_for_portal_ids

            if not record.is_product_visibility_guest_user:
                guest_prods = False
                guest_cats = False
                params.set_str('filter_mode', 'product_only')
            elif record.filter_mode == 'product_only':
                guest_cats = False
            elif record.filter_mode == 'categ_only':
                guest_prods = False

            if not record.is_product_visibility_portal_user:
                portal_prods = False
                portal_cats = False
            elif record.filter_mode_portal == 'product_only':
                portal_cats = False
            elif record.filter_mode_portal == 'categ_only':
                portal_prods = False

            params.set_str(
                'website_product_visibility.available_products_for_guest_ids',
                str(guest_prods.ids if guest_prods else []),
            )
            params.set_str(
                'website_product_visibility.available_products_for_portal_ids',
                str(portal_prods.ids if portal_prods else []),
            )
            params.set_str(
                'website_product_visibility.available_cat_for_guest_ids',
                str(guest_cats.ids if guest_cats else []),
            )
            params.set_str(
                'website_product_visibility.available_cat_for_portal_ids',
                str(portal_cats.ids if portal_cats else []),
            )

    def get_values(self):
        """Retrieve and return configuration parameters dictionary."""
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()

        guest_prods = literal_eval(
            params.get_str(
                'website_product_visibility.available_products_for_guest_ids',
                '[]',
            )
        ) or []
        portal_prods = literal_eval(
            params.get_str(
                'website_product_visibility.available_products_for_portal_ids',
                '[]',
            )
        ) or []
        guest_cats = literal_eval(
            params.get_str(
                'website_product_visibility.available_cat_for_guest_ids',
                '[]',
            )
        ) or []
        portal_cats = literal_eval(
            params.get_str(
                'website_product_visibility.available_cat_for_portal_ids',
                '[]',
            )
        ) or []

        res.update(
            is_product_visibility_guest_user=params.get_bool(
                'is_product_visibility_guest_user'
            ),
            is_product_visibility_portal_user=params.get_bool(
                'is_product_visibility_portal_user'
            ),
            filter_mode=params.get_str('filter_mode') or 'product_only',
            filter_mode_portal=params.get_str('filter_mode_portal') or 'product_only',
            available_products_for_guest_ids=[(6, 0, guest_prods)],
            available_products_for_portal_ids=[(6, 0, portal_prods)],
            available_cat_for_guest_ids=[(6, 0, guest_cats)],
            available_cat_for_portal_ids=[(6, 0, portal_cats)],
        )
        return res
