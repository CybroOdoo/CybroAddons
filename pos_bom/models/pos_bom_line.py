# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class POSBomLines(models.Model):
    """Creating pos_bom_line model to adding pos product bom components"""
    _name = 'pos.bom.line'
    _description = "POS BOM Lines"

    product_id = fields.Many2one('product.product',
                                 string="POS Product Bom",
                                 domain=[('is_bom', '=', False)],
                                 help="Select the product")
    sequence = fields.Integer('Sequence', default=1,
                              help="Gives the sequence order when displaying")
    bom_id = fields.Many2one('pos.product.bom',
                             string="BOM Product",
                             help="Get the bill of material product")
    quantity = fields.Float(string="Quantity",
                            help="Set the quantity of the product")
    product_uom_id = fields.Many2one('uom.uom',
                                     string="Unit of Measure",
                                     help="Add the unit of measure")

    @api.onchange('product_id')
    def onchange_product(self):
        """Onchange the product field"""
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
