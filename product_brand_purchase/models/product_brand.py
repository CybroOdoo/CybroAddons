# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
from odoo import api, fields, models


class ProductBrand(models.Model):
    """
    This class represents a Product Brand in your application.
    It is used to store information about different product brands, including
    their name, an image associated with the brand, and a list of products that
    belong to this brand.
    """
    _name = 'product.brand'
    _description = 'Product Brand'

    name = fields.Char(string="Name", help="Name of the product brand")
    brand_image = fields.Binary(string="Image",
                                help="Image of the product brand")
    member_ids = fields.One2many('product.template', 'brand_id',
                                 string="Member",
                                 help="List of products under the product brand")
    product_count = fields.Char(string='Product Count',
                                compute='_compute_product_count',
                                store=True, help="Number of products")

    @api.depends('member_ids')
    def _compute_product_count(self):
        """
        Compute the number of products associated with this product brand.

        This method is used as a decorator function for the 'product_count'
        field. It calculates the number of products in the 'member_ids'
        one-to-many relationship and updates the 'product_count' field with the
        result.
        """
        for record in self:
            record.product_count = len(record.member_ids)
