# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    """Inherits the Scrap model for adding new field and function"""
    _inherit = 'stock.scrap'

    cw_qty = fields.Float(string='CW-Qty', digits=(16, 4),
                          compute='_compute_cw_qty',
                          help="Catch weight quantity")
    category_id = fields.Many2one('uom.category',string="Category",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                help="Catch weight unit of measure",
                                domain="[('category_id', '=', category_id)]",
                                compute='_compute_cw_uom_id'
                                )
    toggle_cw = fields.Boolean(string='is_cw_product', default=False)

    def _compute_cw_qty(self):
        """computing the qty"""
        if self.product_id.catch_weigth_ok and self.product_id.average_cw_qty != 0:
            self.cw_qty = self.product_id.average_cw_qty * self.scrap_qty
        else:
            self.cw_qty = 0.0

    def _compute_cw_uom_id(self):
        """computing the cw uom id"""
        if self.product_id.catch_weigth_ok:
            self.update({'cw_uom_id': self.product_id.cw_uom_id})

    @api.onchange('product_id', 'scrap_qty')
    def _onchange_product(self):
        """Calculating cw uom ,product uom and cw qty"""
        self.toggle_cw = bool(self.product_id.catch_weigth_ok)
        self.product_uom_id = self.product_id.uom_id
        self.cw_uom_id = self.product_id.cw_uom_id
        self.cw_qty = self.product_id.average_cw_qty * self.scrap_qty

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Calculating scrap qty"""
        self.scrap_qty = 1.0

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Calculating cw qty from scrap qty"""
        if self.product_id.catch_weigth_ok and self.product_id.average_cw_qty != 0:
            if self.cw_uom_id == self.product_uom_id:
                self.scrap_qty = self.cw_qty
            else:
                self.scrap_qty = self.cw_qty / self.product_id.average_cw_qty

    @api.onchange('scrap_qty')
    def _onchange_scrap_qty(self):
        """Calculating scrap qty from cw qty"""
        if self.product_id.catch_weigth_ok and self.product_id.average_cw_qty != 0:
            if self.cw_uom_id == self.product_uom_id:
                self.cw_qty = self.scrap_qty
            else:
                self.cw_qty = self.scrap_qty * self.product_id.average_cw_qty
