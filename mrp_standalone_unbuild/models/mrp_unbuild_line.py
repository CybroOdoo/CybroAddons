# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models 


class MrpUnbuildLine(models.Model):
    """Component lines for auto-update and manual adjustments"""
    _name = 'mrp.unbuild.line'
    _description = 'Unbuild Line'

    unbuild_id = fields.Many2one('mrp.unbuild', string='Unbuild Order', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    qty = fields.Float(string='Quantity', default=1.0, digits='Product Unit')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True,
                             compute='_compute_uom_id', store=True, readonly=False, precompute=True)
    qty_on_hand = fields.Float(string='On Hand', related='product_id.qty_available', readonly=True,
                               help="Current Stock of this product")
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial Number', domain="[('product_id', '=', product_id)]")
    bom_line_id = fields.Many2one('mrp.bom.line', string='BoM Line')
    byproduct_id = fields.Many2one('mrp.bom.byproduct', string='Byproduct')

    @api.depends('product_id')
    def _compute_uom_id(self):
        """Compute Unbuild Order UOM"""
        self.uom_id = False
        for line in self:
            if line.product_id:
                line.uom_id = line.product_id.uom_id
