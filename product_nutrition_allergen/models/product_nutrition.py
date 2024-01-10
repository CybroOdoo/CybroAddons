# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreeshanth V S (odoo@cybrosys.com)
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
##############################################################################
from odoo import fields, models


class ProductNutrition(models.Model):
    """ For managing product nutrition and allergen information"""
    _name = "product.nutrition"
    _description = "Product Nutrition"

    name = fields.Char(string='Nutritional Name',
                       help="Identifying nutritional name")
    nutrition_value = fields.Float(string="Value",
                                   help="Getting nutritional value")
    product_template_id = fields.Many2one('product.template',
                                          string="Product",
                                          help="Inverse fields for nutrition_ids "
                                               "One2many field in product template")
    uom_id = fields.Many2one("uom.uom", string="Unit",
                             help="For getting unit of nutrition value")
