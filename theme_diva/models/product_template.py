# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """Extend the 'product.template' model to include additional
    rating-related fields."""
    _inherit = 'product.template'

    def _count_rating_count(self):
        """Compute the average rating count for each product"""
        for rec in self:
            reviews = rec.rating_get_stats()
            rec.rating_count = reviews.get('avg')

    def _count_rating_total(self):
        """Compute the total rating count for each product."""
        for rec in self:
            reviews = rec.rating_get_stats()
            rec.rating_total = reviews.get('total')

    rating_count = fields.Float(compute='_count_rating_count',
                                string='Average Rating',
                                help="Average rating count for the product.")
    rating_total = fields.Integer(compute='_count_rating_total',
                                  string='Total Rating',
                                  help="Total rating count for the product.")
