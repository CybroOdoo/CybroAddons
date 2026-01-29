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


class ProductFeatured(models.Model):
    """Model for managing featured products on the website."""
    _name = 'product.featured'
    _inherit = ['website.published.mixin', 'mail.thread']
    _description = 'Basic model for featured products records'

    def _default_featured_list_ids(self):
        """Generate a default list of featured products."""
        featured_products = []
        products = self.env['product.template'].search([], limit=8)
        for product in products:
            featured_products.append((0, 0, {
                'product_id': product.id,
                'featured_rel_id': self.id
            }))
        return featured_products

    name = fields.Char(string="Name", help="Name of the featured product")
    is_website_published = fields.Boolean(string='Available on the Website',
                                          copy=False, default=False,
                                          help="Whether the product is "
                                               "available for display on the"
                                               " website")
    featured_list_ids = fields.One2many("product.featured.relation",
                                        "featured_rel_id",
                                        string="Featured List",
                                        default=_default_featured_list_ids,
                                        help="List of related products for"
                                             " featuring")
    user_id = fields.Many2one('res.users', string="Person Responsible",
                              track_visibility='onchange',
                              default=lambda self: self.env.uid,
                              help="User responsible for managing the featured"
                                   " products")
