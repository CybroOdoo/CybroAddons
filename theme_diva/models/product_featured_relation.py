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


class ProductFeaturedRelation(models.Model):
    """Model representing the relationship between featured products and the
     product_featured model."""
    _name = 'product.featured.relation'
    _description = 'Related Model for product_featured table'

    product_id = fields.Many2one('product.template', string="Product",
                                 help="The related product associated with "
                                      "the featured relation.")
    featured_rel_id = fields.Many2one('product.featured',
                                      string="Featured Product",
                                      help="The featured product associated "
                                           "with the relation.")
