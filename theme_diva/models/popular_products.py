# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ashwin T (<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class PopularProducts(models.Model):
    """popular_products"""
    _name = "popular.products"
    _description = "Popular Products"

    name = fields.Char(string="Name", required=True)
    product_ids = fields.Many2many(
        "product.template",
        string="Selected Products",
        domain=[('is_published', '=', True)]
    )
    product_count = fields.Integer(
        string="Product Count",
        help="Number of product variants to be displayed",
        compute="_compute_product_count",
        store=True
    )
    active = fields.Boolean(default=True)

    @api.depends('product_ids', 'product_ids.product_variant_ids', 'product_ids.product_variant_ids.website_published',
                 'product_ids.product_variant_ids.active')
    def _compute_product_count(self):
        """Compute the number of product variants to be displayed"""
        for rec in self:
            # Get manually selected product variants that are published and active
            manual_variants = rec.product_ids.mapped('product_variant_idsproduct_variant_ids').filtered(
                lambda v: v.website_published and v.active
            )

            # Get automatically marked popular product variants
            auto_products = self.env['product.template'].search([
                ('is_popular', '=', True),
                ('is_published', '=', True)
            ])
            auto_variants = auto_products.mapped('product_variant_ids').filtered(
                lambda v: v.website_published and v.active
            )

            # Combine and count unique variants
            rec.product_count = len(manual_variants | auto_variants)

    def get_popular_product_variants(self):
        """Returns published variants of both manually selected and auto-marked popular products"""
        self.ensure_one()
        # Get manually selected product variants
        manual_variants = self.product_ids.mapped('product_variant_ids').filtered(
            lambda v: v.website_published and v.active
        )

        # Get automatically marked popular product variants
        auto_products = self.env['product.template'].search([
            ('is_popular', '=', True),
            ('is_published', '=', True)
        ])
        auto_variants = auto_products.mapped('product_variant_ids').filtered(
            lambda v: v.website_published and v.active
        )

        return (manual_variants | auto_variants)[:self.product_count]
