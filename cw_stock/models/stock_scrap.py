# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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


class StockScrap(models.Model):
    """Inherits Stock Scrap for including fields and functions for Catch
     Weight"""
    _inherit = 'stock.scrap'

    cw_qty = fields.Float(string='CW-Qty', digits=(16, 4), readonly=False,
                          compute='_compute_cw_qty',
                          help="Catch weight quantity")
    category_id = fields.Many2one('uom.category',
                                  string="UoM Category",
                                  help="Category of the Product",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom',
                                related='product_id.cw_uom_id',
                                string='CW-UoM',
                                help="Catch weight unit of measure",
                                domain="[('category_id', '=', category_id)]"
                                )
    toggle_cw = fields.Boolean(related='product_id.catch_weight_ok',
                               string='CW Product',
                               help="True if it is a Catch Weight Product")

    @api.depends('product_id')
    def _compute_cw_qty(self):
        """Method for computing product_uom_id and cw_quantity"""
        for rec in self:
            rec.product_uom_id = rec.product_id.uom_id
            rec.cw_qty = rec.product_id.average_cw_qty * rec.scrap_qty

    @api.onchange('scrap_qty')
    def _onchange_scrap_qty(self):
        """Calculating scrap qty from cw qty"""
        if self.product_id.catch_weight_ok and \
                self.product_id.average_cw_qty != 0:
            self.cw_qty = self.scrap_qty * self.product_id.average_cw_qty

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Method for calculating cw qty from scrap qty"""
        if self.product_id.catch_weight_ok and self.product_id. \
                average_cw_qty != 0:
            self.scrap_qty = self.cw_qty / self.product_id.average_cw_qty
