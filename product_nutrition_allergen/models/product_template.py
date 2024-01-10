# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author : Sreeshanth V S (odoo@cybrosys.com)
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
from odoo import api, fields, models


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

    @api.model
    def product_nutrition_details(self, name):
        """ Return product nutrition details to js"""
        lang = self.env['res.users'].browse(self.env.uid).lang
        product_name = name.split('#')[0].split('-')
        product_info = product_name[len(product_name) - 1]
        product_id = product_info.split('?')[0]
        product = self.browse(int(product_id))
        query = (""" select product_nutrition.name AS name,
                    product_nutrition.nutrition_value,uom_uom.name->> '{}' as 
                    uom_name from product_template join product_nutrition on 
                    product_template.id = product_nutrition.product_template_id 
                    join uom_uom on uom_uom.id = product_nutrition.uom_id """
                 .format(lang))
        if product.nutrition_ids:
            self.env.cr.execute(
                """{} where product_template.id ='{}'""".format(
                    query, product_id))
            conf = self.env.cr.dictfetchall()
            return conf

    @api.model
    def product_ingredients_details(self, name):
        """ Return product ingredient details to js"""
        product_name = name.split('#')[0].split('-')
        product_info = product_name[len(product_name) - 1]
        product_id = product_info.split('?')[0]
        product = self.browse(int(product_id))
        return product.ingredients_information

    @api.model
    def product_allergy_details(self, name):
        """ Return product allergy details to js"""
        product_name = name.split('#')[0].split('-')
        product_info = product_name[len(product_name) - 1]
        product_id = product_info.split('?')[0]
        product = self.browse(int(product_id))
        return product.allergy_information
