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
from odoo import api, fields, models


class ProductBrand(models.Model):
    """Creates product brand"""
    _name = 'product.brand'
    _description = "Product Brand"

    name = fields.Char(string="Name", help="Name of brand", required=True)
    brand_image = fields.Binary(string="Image", help='Image of brand')
    member_ids = fields.One2many('product.template',
                                 'brand_id',
                                 string="Products", help="Product in a brand")
    product_count = fields.Char(string='Product Count',
                                compute='get_count_products', store=True,
                                help="Product count")

    @api.depends('member_ids')
    def get_count_products(self):
        """Show count of products"""
        for brand in self:
            brand.product_count = len(brand.member_ids)
