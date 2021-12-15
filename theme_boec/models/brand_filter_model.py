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

from odoo import models, fields


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = "Product Brand"
    _rec_name = 'brand_name'
    brand_name = fields.Char(required=True)
    sequence_no = fields.Integer(string="Sequence no")
    parent_id = fields.Many2one('product.brand', string='Parent Brand',
                                index=True)


class DiscountPrizeTag(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', string="Product Brand")


class Website(models.Model):
    _inherit = "website"

    def get_brands(self):
        brand = self.env['product.brand'].search([])
        return brand
