# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models


class ProductAddAttribute(models.TransientModel):
    """
        Model for adding Attributes and Variants
    """
    _name = 'product.add.attribute'
    _description = 'Product Add Attribute'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   help='Products which are selected')
    attribute_line_ids = fields.One2many('product.management.attribute',
                                         'wizard_id',
                                         string="Product Attributes",
                                         help='Attribute Lines')

    def action_add_product_attributes(self):
        """
        Function for adding Attributes and Variants for Selected Products
        """
        if self.product_ids and self.attribute_line_ids:
            for products in self.product_ids:
                for line in self.attribute_line_ids:
                    products.attribute_line_ids = [fields.Command.create({
                        'attribute_id': line.attribute_id.id,
                        'value_ids': line.value_ids,
                    })]


class ProductAttribute(models.TransientModel):
    """
    Model for attribute_lines for the model product.add.attribute
    """
    _name = 'product.management.attribute'
    _description = 'Product Attributes'

    attribute_id = fields.Many2one('product.attribute',
                                   string='Attribute',
                                   help='Attribute ID')
    value_ids = fields.Many2many('product.attribute.value',
                                 string='Values',
                                 help='Attribute Values',
                                 domain="[('attribute_id','=',attribute_id)]")
    wizard_id = fields.Many2one('product.add.attribute',
                                string='ID',
                                help='Wizard ID')
