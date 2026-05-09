# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """Inheriting product variants model for adding a field
                        that will hide price from website"""
    _inherit = 'product.template'

    price_call = fields.Boolean(string="Call for Price",
                                help="This will hide the price and cart button"
                                     " from shop and customer can request by "
                                     "calling for price")

    website_hide_variants = fields.Boolean(
        string="Hide on Website",
        compute='_compute_website_hide_variants',
        inverse='_inverse_website_hide_variants',
        store=True,
        help="Check right if you want to hide the variant in your website"
    )

    @api.depends('product_variant_ids.website_hide_variants')
    def _compute_website_hide_variants(self):
        for record in self:
            # Consider hidden if ALL variants are hidden (or maybe any? usually all for a 'template' level flag to be true)
            # Let's say if ANY is visible, the template is "visible" (so check is False).
            # So if ALL are hidden, check is True.
            if not record.product_variant_ids:
                record.website_hide_variants = False
            else:
                record.website_hide_variants = all(record.product_variant_ids.mapped('website_hide_variants'))

    def _inverse_website_hide_variants(self):
        for record in self:
            # If user toggles the template field, apply to ALL variants
            record.product_variant_ids.website_hide_variants = record.website_hide_variants
