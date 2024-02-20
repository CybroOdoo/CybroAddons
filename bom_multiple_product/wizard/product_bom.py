# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (Contact : odoo@cybrosys.com)
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


class ProductBom(models.TransientModel):
    """This class represents a transient model for generating
    a Bill of Materials (BOM) from products. """
    _name = 'product.bom'
    _description = 'BOM from products'

    product_id = fields.Many2one('product.product',
                                 required=True, string='Finished Product',
                                 help='Choose the Finished Product',
                                 domain="[('type', 'in', ['product','consu'])]")
    quantity = fields.Float(string='Quantity',
                            help='Quantity of finished product',
                            required=True, default=1)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    uom_id = fields.Many2one('uom.uom', string='Unit Of Measure',
                             help='Unit of measure of Finished product',
                             required=True, ondelete="restrict",
                             domain="[('category_id', '=', product_uom_category_id)]")
    product_ids = fields.Many2many('product.product',
                                   string='Components',
                                   help='Components Products of BOM')
    bom_type = fields.Selection([
        ('normal', 'Manufacture this product'),
        ('phantom', 'Kit')], 'BoM Type',
        default='normal', required=True, help='The bom type for the product')

    def action_create_bom(self):
        """Create bill of materials from products"""
        line_vals = [(0, 0, {'product_id': rec.id,
                             'product_qty': 1
                             }) for rec in self.product_ids]
        bom_id = self.env['mrp.bom'].sudo().create({
            'product_id': self.product_id.id,
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'product_qty': self.quantity,
            'product_uom_id': self.uom_id.id,
            'type': self.bom_type,
            'bom_line_ids': line_vals
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'view_mode': 'form',
            'res_id': bom_id.id,
        }
