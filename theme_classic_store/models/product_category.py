# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vivek @ cybrosys,(odoo@cybrosys.com)
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
from odoo import fields, models


class ProductPublicCategory(models.Model):
    """
    Adding 'category_count' field to the 'product.public.category' model.
    """
    _inherit = 'product.public.category'

    category_count = fields.Integer(string="Count",
                                    help="The count of different products in each category.",
                                    compute="_compute_category_count")

    def _compute_category_count(self):
        """
        Compute function for calculating the value of category_count
        Calculates the count of different products in each category
        """
        product_ids = self.env['product.template'].search(
            [('website_published', '=', True)])
        for category in self:
            category_ids = category.search(
                [('id', 'child_of', category.id)]).ids
            category.category_count = sum(
                1 for rec in product_ids for cat in rec.public_categ_ids if
                cat.id in category_ids)


class Product(models.Model):
    """
    Adding 'views' and 'most_viewed' fields to the 'product.template' model
    """
    _inherit = 'product.template'

    views = fields.Integer(string="Views",
                           help="The total views for the product through website.")
    most_viewed = fields.Boolean(string="Most Viewed",
                                 help='Set true if the product is most viewed')
