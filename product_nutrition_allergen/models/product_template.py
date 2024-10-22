# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author : Manasa T P (odoo@cybrosys.com)
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


class ProductTemplate(models.Model):
    """ Added product nutrition information"""
    _inherit = "product.template"

    nutrition_details = fields.Boolean(string="Nutrition Details",
                                       help="Enable to add nutrition "
                                            "information")
    allergy_details = fields.Boolean(string="Allergy Details",
                                     help="Enable to add allergy information")
    ingredients_details = fields.Boolean(string="Ingredients Details",
                                         help="Enable to add ingredients "
                                              "details")
    nutrition_amount = fields.Float(string="Nutrition as Per",
                                    help="Nutrition amount per unit")
    unit_id = fields.Many2one('uom.uom', string="Unit",
                              help="Nutrition unit")
    nutrition_ids = fields.One2many('product.nutrition',
                                    'product_template_id',
                                    string="Nutrition",
                                    help="Adding nutrition information in"
                                         "product")
    ingredients_information = fields.Text(string="Ingredients Information",
                                          help="Ingredients Information")
    allergy_information = fields.Text(string="Allergy Information",
                                      help="Allergy Information")
