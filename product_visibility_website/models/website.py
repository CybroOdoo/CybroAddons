# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solution (<https://www.cybrosys.com>)
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


class Website(models.Model):
    """Extends the 'website' model to filter product search."""
    _inherit = "website"
    _description = "Website"

    def _search_with_fuzzy(self, search_type, search, limit, order, options):
        """This method extends the base search functionality to include
         additional filtering"""
        res = super()._search_with_fuzzy(search_type, search, limit, order, options)
        response = list(res)
        Product = self.env['product.template']
        Category = self.env['product.public.category']
        user = self.env.user
        target = next((d for d in response[1] if d.get('model') == 'product.public.category'), None)
        pdt_target = next((d for d in response[1] if d.get('model') == 'product.template'), None)
        if target or pdt_target:
            available_products, available_categ, parent_categs = self.get_available_product_categories(user)
            mode = self.get_user_mode(user, available_products, available_categ)
            if mode == 'product_only':
                if target:
                    product_category = available_products.mapped('public_categ_ids')
                    category = set(target['results'].ids).intersection(set(product_category.ids))
                    target['results'] = Category.browse(category)
                if pdt_target:
                    products = set(pdt_target['results'].ids).intersection(set(available_products.ids))
                    final_products = Product.search([('id', 'in', list(products))], order=order)
                    pdt_target['results'] = final_products
                    response[0] = len(final_products)
            if mode == 'categ_only':
                categ_products = available_categ.mapped('product_tmpl_ids') | Category.search(
                    [('id', 'child_of', available_categ.ids)]).mapped('product_tmpl_ids')
                products = set(pdt_target['results'].ids).intersection(set(categ_products.ids))
                if target:
                    category = set(target['results'].ids).intersection(set(available_categ.ids))
                    target['results'] = Category.browse(category)
                if pdt_target:
                    final_products = Product.search([('id', 'in', list(products))], order=order)
                    pdt_target['results'] = final_products
                    response[0] = len(final_products)
        return tuple(response)

    def get_available_product_categories(self, user):
        """Fetch and return all the category based on user given
        :params user: current login user
        :returns: the product and categories based on the configuration of visibility"""
        Product = available_products = self.env['product.template']
        Category = parent_categs = available_categ = self.env['product.public.category']
        parent_ids = []
        if (not user or user._is_public()) and self.env['ir.config_parameter'].sudo().get_param(
                'website_product_visibility.product_visibility_guest_user', False):
            available_products = literal_eval(
                self.env['ir.config_parameter'].sudo().get_param(
                    'website_product_visibility.available_products_for_guest_ids',
                    Product))
            available_categ = literal_eval(
                self.env['ir.config_parameter'].sudo().get_param(
                    'website_product_visibility.available_cat_for_guest_ids',
                    Category))
        else:
            partner = user.partner_id
            if partner.product_visibility:
                available_products = partner.website_available_product_ids
                available_categ = partner.website_available_cat_ids
        if not available_categ and not available_products and \
                self.env.user.has_group('base.group_portal') and self.env[
            'ir.config_parameter'].sudo().get_param(
            'website_product_visibility.product_visibility_portal_user', False):
            available_products = literal_eval(
                self.env['ir.config_parameter'].sudo().get_param(
                    'website_product_visibility.available_products_for_portal_ids', Product))
            available_categ = literal_eval(
                self.env['ir.config_parameter'].sudo().get_param(
                    'website_product_visibility.available_cat_for_portal_ids', Category))
        if isinstance(available_categ, list):
            available_categ = Category.browse(available_categ)
        if isinstance(available_products, list):
            available_products = Product.browse(available_products)
        if available_categ:
            # Collect all parent IDs in one pass
            parent_ids = set(
                int(pid)
                for categ in available_categ
                if categ and categ.parent_path
                for pid in categ.parent_path.split('/')[:-1]
            )
        elif available_products:
            product_category = available_products.mapped('public_categ_ids')
            # Collect all parent IDs in one pass from the category for the products we got
            parent_ids = set(
                int(pid)
                for categ in product_category
                if categ and categ.parent_path
                for pid in categ.parent_path.split('/')[:-1]
            )
        if parent_ids:
            # Browse once and merge the parent categories
            parent_categs = self.env['product.public.category'].browse(parent_ids)
        return available_products, available_categ, parent_categs

    def get_user_mode(self, user, available_products, available_categ):
        """Get the user mode to filter out the products and category
        :params user: current loged in user
        :params available_products: list of products to be filtered out
        :params available_categ: list of category to be filtered out
        :returns: the user mode whether based on category or product and also based on partner record or on the
        options in res.config.settings
        """
        mode = False
        if (not user or user._is_public()) and self.env['ir.config_parameter'].sudo().get_param(
                'website_product_visibility.product_visibility_guest_user', False):
            mode = self.env['ir.config_parameter'].sudo().get_param('filter_mode')
        else:
            partner = user.partner_id
            if partner.product_visibility:
                mode = partner.filter_mode
        if not available_categ and not available_products and \
                self.env.user.has_group('base.group_portal') and self.env[
            'ir.config_parameter'].sudo().get_param(
            'website_product_visibility.product_visibility_portal_user', False):
            mode = self.env['ir.config_parameter'].sudo().get_param('filter_mode_portal')
        return mode
