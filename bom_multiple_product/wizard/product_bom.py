# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ProductBom(models.TransientModel):
    """ Model create bom directly from products variants """
    _name = 'product.bom'
    _description = 'BOM From Products'

    product_id = fields.Many2one(
        'product.product', string='Finished Product',
        required=True,
        help='The Product we want to Manufacture',
        domain="[('type', 'in', ['product', 'consu'])]")
    quantity = fields.Float(
        string='Quantity',
        help='Choose The Quantity of Finished Product',
        required=True, default=1)
    uom_id = fields.Many2one(
        'uom.uom', string='Unit Of Measure',
        help='Select the Unit of Measure of Finished Product',
        required=True)
    product_ids = fields.Many2many(
        'product.product', string='Components',
        help='The selected products for bom')

    def action_create_bom(self):
        """Create bill of materials from products"""
        self.env['mrp.bom'].sudo().create({
            'product_id': self.product_id.id,
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'product_qty': self.quantity,
            'product_uom_id': self.uom_id.id,
            'bom_line_ids': [(0, 0, {'product_id': rec.id,
                                     'product_qty': 1
                                     }) for rec in self.product_ids]
        })
