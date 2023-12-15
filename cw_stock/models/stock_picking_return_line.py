# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class StockReturnPickingLine(models.TransientModel):
    """Inherits Stock Return Picking Line for including the Catch Weight fields
     and functions"""
    _inherit = "stock.return.picking.line"

    cw_qty = fields.Float(string='CW-Qty ', compute="_compute_cw_qty",
                          help="Catch weight quantity", digits=(16, 4))
    category_id = fields.Many2one('uom.category', string="Category",
                                  help="Category of the Product",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom',
                                related='product_id.cw_uom_id',
                                string='CW-UoM',
                                help="Unit of Measure of Catch Weight",
                                domain="[('category_id', '=', category_id)]")
    cw_hide = fields.Boolean(related='product_id.catch_weight_ok',
                             string='CW Product',
                             help="True if it is a Catch weight product")

    @api.depends('product_id', 'quantity')
    def _compute_cw_qty(self):
        """Calculating cw qty done"""
        for rec in self:
            if rec.product_id.catch_weight_ok:
                rec.cw_qty = rec.quantity * rec.product_id.average_cw_qty

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Calculating cw qty from qty"""
        if self.product_id.catch_weight_ok and self.product_id.average_cw_qty \
                != 0:
            self.quantity = self.cw_qty / self.product_id.average_cw_qty
