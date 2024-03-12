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
from odoo import api, fields, models


class SimpleMRPBom(models.Model):
    """Creates the model simple.mrp.bom"""
    _name = 'simple.mrp.bom'
    _description = "Bills of Materials"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string="Product",
                                 required=True, help="Name of the product")
    product_qty = fields.Float(string="Quantity", default=1.0, tracking=True,
                               help="Quantity of products")
    uom_id = fields.Many2one('uom.uom', string='Product Unit of Measure',
                             required=True,
                             help="Unit of measurement for product")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 index=True, required=True,
                                 help="Company corresponding to the product")
    line_ids = fields.One2many('simple.mrp.bom.line', 'bom_id',
                               string="Components",
                               help="Components used to create the product")

    @api.onchange('product_id')
    def onchange_product_id(self):
        """ Update the Uom for the product """
        self.uom_id = self.product_id.uom_id.id
