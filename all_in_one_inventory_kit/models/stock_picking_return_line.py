# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
    _inherit = "stock.return.picking.line"

    cw_qty = fields.Float(string='CW-Qty ', compute="_compute_cw_qty",
                          help="Catch weight quantity", digits=(16, 4))
    category_id = fields.Many2one('uom.category', string="Category",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'),
                                  help="Category")
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                domain="[('category_id', '=', category_id)]",
                                compute='_compute_cw_uom_id',
                                readonly=True,
                                help="Catch weight unit of measure")
    cw_hide = fields.Boolean(string='Is CW Product',
                             compute="_compute_cw_hide",
                             default=False, help="Catch weight hide")

    @api.depends('product_id')
    def _compute_cw_hide(self):
        """ Computes the cw_hide feature"""
        for rec in self:
            rec.cw_hide = bool(rec.product_id.catch_weight_ok)

    @api.depends('product_id')
    def _compute_cw_uom_id(self):
        """Calculating cw uom"""
        for rec in self:
            if rec.product_id.catch_weight_ok:
                rec.cw_uom_id = rec.product_id.cw_uom_id
            else:
                rec.cw_uom_id = None

    @api.depends('product_id', 'quantity')
    def _compute_cw_qty(self):
        """Calculating cw qty done"""
        for rec in self:
            if rec.product_id.catch_weight_ok:
                if rec.cw_uom_id == rec.uom_id:
                    rec.quantity = rec.cw_qty
                else:
                    rec.cw_qty = rec.quantity * rec.product_id.average_cw_qty

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Calculating cw qty from qty"""
        for rec in self:
            if rec.product_id.catch_weight_ok and rec.product_id.average_cw_qty\
                    != 0:
                if rec.cw_uom_id == rec.uom_id:
                    rec.quantity = rec.cw_qty
                else:
                    rec.quantity = rec.cw_qty / rec.product_id.average_cw_qty
