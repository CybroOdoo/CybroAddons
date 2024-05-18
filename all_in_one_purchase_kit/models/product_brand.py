# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
#
###############################################################################
from odoo import api, fields, models


class ProductBrand(models.Model):
    """Model to add brand for products"""
    _name = 'product.brand'
    _description = 'Product Brand'

    name = fields.Char(String="Name", help="Brand name")
    brand_image = fields.Binary(String="Brand Logo", help="Brand Logo")
    product_ids = fields.One2many(
        'product.template', 'brand_id', string="Product", help="Add product"
    )
    product_count = fields.Char(
        String='Product Count', compute='_compute_count_products', store=True,
        help="Count of Products"
    )

    @api.depends('product_ids')
    def _compute_count_products(self):
        """Methode to get the count of products in brand"""
        for rec in self:
            rec.product_count = len(rec.product_ids)
