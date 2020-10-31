# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, api, fields, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    published_count = fields.Integer(string="Published", compute='compute_count')
    unpublished_count = fields.Integer(string="Unpublished", compute='compute_count')

    def compute_count(self):
        for rec in self:
            products = self.env['product.template'].search([('categ_id', '=', rec.id)])
            published = products.filtered(lambda product: product.is_published == True and product.sale_ok == True)
            unpublished = products.filtered(lambda product: product.is_published == False and product.sale_ok == True)
            rec.published_count = len(published)
            rec.unpublished_count = len(unpublished)

    def action_publish_all_products(self):
        for rec in self:
            products = self.env['product.template'].search([('categ_id', '=', rec.id)])
            products = products.filtered(lambda product: product.sale_ok == True)
            for product in products:
                if not product.is_published:
                    product.is_published = True

