# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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

    parent_category_id = fields.Many2one("product.category",
                                         string="Parent Category")
    is_category = fields.Boolean(default=True)
    category_id = fields.Char(string='Parent Category',
                              compute="_compute_category_id")

    @api.depends('is_category')
    def _compute_category_id(self):
        """ Get the parent category of the product"""
        self.category_id = self.categ_id.parent_id.id

    @api.model
    def search_products(self, qry):
        """ Search all products in product.template,
        and pass searched products into templates """
        qry = (qry or '').strip()
        if not qry:
            return []
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
        qry = (qry or '').strip()
        if not qry:
            return []
        excluded = []
        for xmlid in [
            'product.product_category_goods',
            'product.product_category_services',
            'product.product_category_expenses',
        ]:
            rec = self.env.ref(xmlid, raise_if_not_found=False)
            if rec:
                excluded.append(rec.id)

        # Search all categories except base ones, filtered by query
        categories = self.env['product.category'].search([
            ('id', 'not in', excluded),
            ('name', 'ilike', qry)
        ])
        return [[category.name, category.id, category.parent_id.name,
                 category.parent_id.id,
                 category.product_count]
                for category in categories]

    @api.model
    def search_all_categories(self):
        """ Search products in all categories """
        products = self.env['product.template'].search([])
        return [[product.name, product.id,
                 product.list_price,
                 '/web/image/product.template/{}/image_512/'.format(product.id),
                 product.currency_id.symbol, ]
                for product in products]

    @api.model
    def product_all_categories(self):
        """ Search all product categories """
        exclude_xmlids = [
            'product.product_category_goods',
            'product.product_category_services',
            'product.product_category_expenses',
        ]

        excluded_ids = []
        for xmlid in exclude_xmlids:
            rec = self.env.ref(xmlid, raise_if_not_found=False)
            if rec:
                excluded_ids.append(rec.id)

        categories = self.env['product.category'].search([
            ('id', 'not in', excluded_ids)
        ])
        return [[category.name, category.id, category.parent_id.name,
                 category.parent_id.id, category.product_count]
                for category in categories]
