# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
################################################################
from odoo import api, fields, models


class ProductBrand(models.Model):
    """Creates product brand"""
    _name = 'product.brand'
    _description = "Product Brand"

    name = fields.Char(string="Name", help="Name of brand", required=True)
    brand_image = fields.Binary(string="Image", help='Image of brand')
    member_ids = fields.One2many('product.template',
                                 'brand_id',
                                 string="Products", help="Products in a brand")
    product_count = fields.Char(string='Product Count',
                                compute='_compute_get_count_products', store=True,
                                help="Count of the products")

    @api.depends('member_ids')
    def _compute_get_count_products(self):
        """Show count of products"""
        self.product_count = len(self.member_ids)
