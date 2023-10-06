# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """ Inherit product_template model for fetch products and categories to
    frontend"""
    _inherit = 'product.template'

    parent_category_id = fields.Many2one("product.category",string="Parent Category")
    category_boolean = fields.Boolean(default=True)
    category_id = fields.Char(string='Parent Category',compute="_compute_parent_id")

    @api.depends('category_boolean')
    def _compute_parent_id(self):
        """ Get the parent category of the product"""
        self.category_id = self.categ_id.parent_id.id

    @api.model
    def search_products(self, qry):
        """ Search all products in product.template,
        and pass searched products into templates """
        products = self.env['product.template'].search([('name', 'ilike', qry)])
        return [[product.name, product.id,
                 product.list_price,
                 '/web/image/product.template/{}/image_512/'.format(product.id),
                 product.currency_id.symbol, ]
                for product in products]

    @api.model
    def product_category(self, qry):
        """ Search all category in product_category,
        and pass category into another template """
        category = self.env['product.category'].search(
            [('id', '!=', self.env.ref('product.product_category_all').id),
             ('name', 'ilike', qry)])
        return [[category.name, category.id, category.parent_id.name, category.parent_id.id,
                 category.product_count]
                for category in category]
