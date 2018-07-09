# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, _


class FeaturedProducts(models.Model):
    _name = 'product.featured.relation'
    _description = 'Related Model for product_featured table'

    product = fields.Many2one('product.template')
    featured_rel = fields.Many2one('product.featured')


class WebsiteProductFeatured(models.Model):
    _name = 'product.featured'
    _inherit = ['website.published.mixin', 'mail.thread', 'ir.needaction_mixin']
    _description = 'Basic model for featured products records'

    name = fields.Char(string="Name")
    website_published = fields.Boolean(string='Available on the Website', copy=False, default=False)
    featured_list = fields.One2many("product.featured.relation", "featured_rel", string="Featured List")
    user_id = fields.Many2one('res.users', string="Person Responsible", track_visibility='onchange',
                              default=lambda self: self.env.uid)
