# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: SANJAY P (odoo@cybrosys.com)
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
#############################################################################
"""Customized models for Theme Cordage."""
from odoo import models


class ProductTemplate(models.Model):
    """Inherit product template to add custom recommendation logic for Theme Cordage."""
    _inherit = 'product.template'

    def _get_you_might_also_like_products(self, limit=4):
        """
        Fetch up to `limit` recommended products.
        Priority:
        1. Products in the same category.
        2. Products sharing similar tags.
        3. Fallback to recently published products.
        """
        self.ensure_one()
        website = self.env['website'].get_current_website()
        base_domain = [
            ('id', '!=', self.id),
            ('is_published', '=', True),
            ('website_id', 'in', (False, website.id))
        ]
        # Option 1: same category
        category_ids = self.public_categ_ids.ids
        res_products = self.env['product.template']
        if category_ids:
            res_products = self.search(base_domain + [
                ('public_categ_ids', 'in', category_ids)
            ], limit=limit)
        # Option 2: same tags
        if len(res_products) < limit and self.product_tag_ids:
            needed = limit - len(res_products)
            tag_products = self.search(base_domain + [
                ('product_tag_ids', 'in', self.product_tag_ids.ids),
                ('id', 'not in', res_products.ids)
            ], limit=needed)
            res_products |= tag_products
        # Option 3 & Fallback: recently published products
        if len(res_products) < limit:
            needed = limit - len(res_products)
            fallback_products = self.search(base_domain + [
                ('id', 'not in', res_products.ids)
            ], order='write_date desc, id desc', limit=needed)
            res_products |= fallback_products
        return res_products
