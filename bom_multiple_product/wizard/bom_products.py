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


class BomProducts(models.TransientModel):
    _name = 'bom.products'
    _description = 'BOM products'

    bom_id = fields.Many2one('mrp.bom', help='Corresponding Bill of Material')
    product_ids = fields.Many2many('product.product', string='Products')

    def add_components(self):
        """Add components to the bom line"""
        for rec in self.product_ids:
            vals = {
                'product_id': rec.id,
                'product_qty': 1,
            }
            self.bom_id.sudo().write(
                {'bom_line_ids': [(0, 0, vals)]})


class ProductBomCreate(models.TransientModel):
    _name = 'product.bom.create'
    _description = 'BOM from products'

    product_id = fields.Many2one('product.product', string='Finished Product',
                                 required=True, domain="[('type', 'in', ['product', 'consu'])]")
    quantity = fields.Float(string='Quantity', required=True, default=1)
    uom_id = fields.Many2one('uom.uom', string='Unit Of Measure', required=True)

    def create_bom(self):
        """Create bill of materials from products"""
        orders = self.env['product.product'].browse(
            self._context.get('active_ids'))

        line_vals = [(0, 0, {'product_id': rec.id,
                             'product_qty': 1
                             }) for rec in orders]

        self.env['mrp.bom'].sudo().create({
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'product_qty': self.quantity,
            'product_uom_id': self.uom_id.id,
            'bom_line_ids': line_vals
        })
