# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    _name = 'pos.product.bom'
    _rec_name = 'product_id'
    _description = "POS Product BOM"

    name = fields.Char(string="Name", )
    product_id = fields.Many2one('product.template', string="Product", domain=[('is_bom', '=', True)],
                                 required=True)
    reference = fields.Char(string="Reference")
    quantity = fields.Float(string="Quantity", required=True)
    product_uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    bom_line_ids = fields.One2many('pos.bom.line', 'bom_id', string="Components")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancelled')], string='State', readonly='True', default='draft')

    def action_confirm(self):
        self.state = 'confirm'

    def action_cancel(self):
        self.state = 'cancel'

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id


class POSBomLines(models.Model):
    _name = 'pos.bom.line'
    _description = "POS BOM Lines"

    product_id = fields.Many2one('product.product', string="POS Product Bom",domain=[('is_bom', '=', False)],)
    sequence = fields.Integer(
        'Sequence', default=1,
        help="Gives the sequence order when displaying.")
    bom_id = fields.Many2one('pos.product.bom', string="BOM Product")
    quantity = fields.Float(string="Quantity")
    product_uom_id = fields.Many2one('uom.uom', string="Unit of Measure")

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
