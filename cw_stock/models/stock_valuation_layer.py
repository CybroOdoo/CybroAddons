# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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


class StockValuationLayer(models.Model):
    """Inherits the StockValuationLayer class for adding
    fields and methods to the model"""
    _inherit = 'stock.valuation.layer'

    cw_qty_done = fields.Float(string='CW-Qty Done',
                               compute='_compute_cw_qty_done', digits=(16, 4))
    category_id = fields.Many2one('uom.category',string="Category",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                domain="[('category_id', '=', category_id)]",
                                compute='_compute_cw_uom_id')
    cw_hide = fields.Boolean(string='Is CW Product',
                             compute="_compute_hide", default=False)

    @api.depends('product_id')
    def _compute_cw_uom_id(self):
        """Calculating cw uom"""
        for rec in self:
            if rec.product_id.catch_weigth_ok:
                rec.cw_uom_id = rec.product_id.cw_uom_id
            else:
                rec.cw_uom_id = None

    @api.depends('product_id')
    def _compute_hide(self):
        """Computed the cw hide field value"""
        for rec in self:
            rec.cw_hide = bool(rec.product_id.catch_weigth_ok)

    @api.depends('product_id', 'quantity')
    def _compute_cw_qty_done(self):
        """Calculating cw qty done"""
        for rec in self:
            if rec.product_id.catch_weigth_ok:
                rec.cw_qty_done = rec.quantity * rec.product_id.average_cw_qty
            else:
                rec.cw_qty_done = 0
