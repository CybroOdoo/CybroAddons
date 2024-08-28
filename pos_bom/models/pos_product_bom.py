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


class POSProductBOM(models.Model):
    """Creating the pos_product_bom model and adding the product details."""
    _name = 'pos.product.bom'
    _rec_name = 'product_id'
    _description = "POS Product BOM"

    name = fields.Char(string="Name", help="Get the name" )
    product_id = fields.Many2one('product.template', string="Product", domain=[('is_bom', '=', True)],
                                 required=True, help="Select a product for have bom")
    reference = fields.Char(string="Reference", help="Add the reference")
    quantity = fields.Float(string="Quantity", required=True, help="Set the quantity of product")
    product_uom_id = fields.Many2one('uom.uom', string="Unit of Measure", help="Unit of measure of the product")
    bom_line_ids = fields.One2many('pos.bom.line', inverse_name='bom_id', string="Components",
                                   help="Get the bill of material lines")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancelled')], string='State', default='draft', help="State of the pos product bom")

    def action_confirm(self):
        """ confirm button"""
        self.state = 'confirm'

    def action_cancel(self):
        """ Cancel button"""
        self.state = 'cancel'

    @api.onchange('product_id')
    def onchange_product_id(self):
        """Onchange the product field"""
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
