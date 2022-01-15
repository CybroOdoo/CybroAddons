# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
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

from odoo import models, fields, api


class DiscountLimitCategory(models.Model):
    _inherit = 'pos.category'

    discount_limit = fields.Char(string="Discount Limit(%)")
    apply_limit = fields.Boolean()


class RestrictDiscount(models.Model):
    _inherit = 'hr.employee'

    has_pos_discount_control = fields.Boolean("Discount Control")


class ProductDiscountLimit(models.Model):
    _inherit = 'product.product'
    _inherit = 'product.template'

    pd_apply_limit = fields.Boolean()
    product_discount_limit = fields.Char(string="Discount Limit(%)")


class DiscountLimit(models.Model):
    _inherit = 'pos.config'

    apply_discount_limit = fields.Selection([
        ('product', 'Product'),
        ('product_category', 'Product Category')], string="Apply Discount Limit")

    @api.onchange('apply_discount_limit')
    def onchange_apply_discount_limit(self):
        products = self.env['product.product'].search([('available_in_pos', '=', True)])
        categories = self.env['pos.category'].search([])
        if self.apply_discount_limit == 'product':
            for product in products:
                product.pd_apply_limit = True
            for category in categories:
                category.apply_limit = False
        else:
            for category in categories:
                category.apply_limit = True
            for product in products:
                product.pd_apply_limit = False



