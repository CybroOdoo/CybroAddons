# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields


class FeaturedProducts(models.Model):
    _name = 'product.featured.relation'
    _description = 'Featured Products'

    product_id = fields.Many2one('product.template', string="Product",
                                 help="Product")
    featured_rel_id = fields.Many2one('product.featured',
                                      string="Featured Product",
                                      help="Featured Product")


class WebsiteProductFeatured(models.Model):
    _name = 'product.featured'
    _inherit = ['website.published.mixin', 'mail.thread']
    _description = 'Basic model for featured products records'

    def _default_featured_list(self):
        """This function is used to get the featured list"""
        featured_products = []
        products = self.env['product.template'].search([], limit=8)
        for product in products:
            featured_products.append((0, 0, {
                'product_id': product.id,
                'featured_rel_id': self.id
            }))
        return featured_products

    name = fields.Char(string="Name", help='Name')
    website_published = fields.Boolean(string='Available on the Website',
                                       copy=False, default=False,
                                       help='helps to know whether the product'
                                            ' is available on the website')
    featured_list_ids = fields.One2many("product.featured.relation",
                                        "featured_rel_id",
                                        string="Featured List",
                                        default=_default_featured_list)
    user_id = fields.Many2one('res.users', string="Person Responsible",
                              track_visibility='onchange',
                              help='Person Responsible',
                              default=lambda self: self.env.uid)
