# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, _


class FeaturedProducts(models.Model):
    _name = 'product.featured.relation'
    _description = 'Related Model for product_featured table'

    product = fields.Many2one('product.template')
    featured_rel = fields.Many2one('product.featured')


class WebsiteProductFeatured(models.Model):
    _name = 'product.featured'
    _inherit = ['website.published.mixin', 'mail.thread']
    _description = 'Basic model for featured products records'

    def _default_featured_list(self):
        featured_products = []
        products = self.env['product.template'].search([], limit=8)

        for product in products:
            featured_products.append((0, 0, {
                'product': product.id,
                'featured_rel': self.id
            }))
        return featured_products

    name = fields.Char(string="Name")
    website_published = fields.Boolean(string='Available on the Website',
                                       copy=False, default=False)
    featured_list = fields.One2many("product.featured.relation", "featured_rel",
                                    string="Featured List",
                                    default=_default_featured_list)
    user_id = fields.Many2one('res.users', string="Person Responsible",
                              track_visibility='onchange',
                              default=lambda self: self.env.uid)
