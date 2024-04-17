# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Ayana KP (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class MaterialUsed(models.Model):
    """Model for material used in car workshop """
    _name = 'material.used'
    _description = 'Material Used in Car Workshop'

    material_product_id = fields.Many2one('product.product',
                                          string='Products',
                                          help="Product used for work")
    company_id = fields.Many2one('res.company', string='Company',
                                 help='The company of material',required=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one(string='Company Currency',readonly=True,
                                  related='company_id.currency_id',
                                  help='The currency of the company')
    quantity = fields.Integer(string='Quantity', help='Amount for material used')
    price = fields.Monetary(string='Unit Price', help='Unit price for material')
    material_id = fields.Many2one('car.workshop',
                                  help='The work details of material')

    @api.onchange('material_product_id')
    def _onchange_material_product_id(self):
        """ Function for update total price"""
        self.price = self.material_product_id.lst_price
