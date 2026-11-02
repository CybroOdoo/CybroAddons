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
from odoo import api, fields, models


class ProductBrand(models.Model):
    """
    This class represents a brand for products.
    It allows you to define a brand with a name and an optional image,
    and associate it with multiple product templates. The product_count field
    automatically calculates the number of products associated with this brand.
    """
    _name = 'product.brand'
    _description = "Product Brand"

    name = fields.Char(required=True, help="Add name of brand")
    brand_image = fields.Binary(help="Add image of brand")
    member_ids = fields.One2many('product.template', 'brand_id',
                                 help="Choose products")
    product_count = fields.Integer(compute='_compute_product_count',
                                   store=True,
                                   help="Number of products with brand")

    @api.depends('member_ids')
    def _compute_product_count(self):
        """Compute the count of products associated with this brand."""
        for rec in self:
            rec.product_count = len(rec.member_ids)
