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
    """ This class represents a transient model for managing Bill of Materials
     (BOM) products. """
    _name = 'bom.products'
    _description = 'BOM products'

    bom_id = fields.Many2one('mrp.bom', string='Bom Id',
                             help='It is the Corresponding Bill of Material')
    product_ids = fields.Many2many('product.product',
                                   string='Products',
                                   help='Select Component Products of BOM')

    def action_add_components(self):
        """Add components to the bom line"""
        for rec in self.product_ids:
            vals = {
                'product_id': rec.id,
                'product_qty': 1,
            }
            self.bom_id.sudo().write(
                {'bom_line_ids': [(0, 0, vals)]})
