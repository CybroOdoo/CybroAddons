# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj(<https://www.cybrosys.com>)
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
from odoo import api, models, fields


class SimpleMRPBomLine(models.Model):
    """Creates the model simple.mrp.bom line"""
    _name = 'simple.mrp.bom.line'
    _description = "Bills of Materials Components"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    product_id = fields.Many2one('product.product', string="Product",
                                 required=True, help="Product Name")
    product_qty = fields.Float(string="Quantity", default=1.0, tracking=True,
                               help="Quantity of products")
    uom_id = fields.Many2one('uom.uom', string='Product Unit of Measure',
                             required=True,
                             help="Unit of measure of the product")
    bom_id = fields.Many2one('simple.mrp.bom', string="Bill of Material",
                             help="Corresponding Bill of Material")

    @api.onchange('product_id')
    def onchange_product_id(self):
        """ Update the Uom for the product """
        self.uom_id = self.product_id.uom_id.id
