# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhil Ashok(<https://www.cybrosys.com>)
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
from odoo import fields, models


class VariantsTree(models.Model):
    """
    Model representing a variants tree.
    This model is used to define the different variants of a product
     template based on attributes and their values.
    Each variant is associated with a product template and has an attribute,
     a set of values, an extra price, and an
    active flag.
    """
    _name = 'variants.tree'
    _description = "Choose Attributes And Values"

    variants_id = fields.Many2one('product.template', string="Variants",
                                  help="Choose variants")
    attribute_id = fields.Many2one('product.attribute', string='Attribute',
                                   ondelete='restrict', required=True,
                                   index=True, help="Choose Attribute")
    value_ids = fields.Many2many('product.attribute.value', string='Values',
                                 help="Choose value")
    extra_price = fields.Float(string="Price Extra",
                               help="Add extra Price for variants")
