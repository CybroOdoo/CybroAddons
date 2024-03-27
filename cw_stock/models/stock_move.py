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


class StockMove(models.Model):
    """Inherits the stock move model for adding new fields and functions"""
    _inherit = 'stock.move'

    category_id = fields.Many2one('uom.category', string="Category",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                help="Catch weight unit of measure",
                                domain="[('category_id', '=', category_id)]")
    cw_demand = fields.Float(string='CW-Demand', default=1.0, required=True,
                             digits=(16, 4),
                             compute='_cal_cw_demand')
    cw_reserved = fields.Float(string='CW-Reserved', compute='_cal_cw_demand',
                               digits=(16, 4))
    cw_done = fields.Float(string='CW-Done', digits=(16, 4))
    cw_hide = fields.Boolean(string='Is CW Product',
                             compute="_compute_hide", default=False)

    @api.depends('product_id')
    def _compute_hide(self):
        """Compute method for product setups"""
        for rec in self:
            if rec.product_id.catch_weigth_ok:
                rec.cw_hide = rec.product_id.catch_weigth_ok
            else:
                rec.cw_hide = False

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id(self):
        """Calculating cw demand and cw uom"""
        for rec in self:
            rec.cw_demand = rec.product_uom_qty * rec.product_id.average_cw_qty
            rec.name = rec.product_id.default_code
            if rec.product_id.catch_weigth_ok:
                rec.cw_uom_id = rec.product_id.cw_uom_id
            else:
                rec.cw_uom_id = None

    @api.onchange('cw_done')
    def _onchange_cw_done(self):
        """Calculating done qty"""
        for rec in self:
            if rec.product_id.catch_weigth_ok and rec.product_id.average_cw_qty != 0:
                rec.quantity = rec.cw_done / rec.product_id.average_cw_qty

    @api.onchange('quantity_done')
    def _onchange_cw_cty(self):
        """Calculating cw done"""
        for rec in self:
            if rec.product_id.catch_weigth_ok:
                rec.cw_done = rec.quantity * rec.product_id.average_cw_qty

    @api.onchange('cw_demand')
    def _onchange_cw_demand(self):
        """Calculating cw qty"""
        for rec in self:
            if rec.product_id.catch_weigth_ok and rec.product_id.average_cw_qty != 0:
                if rec.cw_uom_id == rec.product_uom:
                    rec.product_uom_qty = rec.cw_demand
                else:
                    rec.product_uom_qty = rec.cw_demand / rec.product_id.average_cw_qty

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        """Calculating cw demand"""
        for rec in self:
            if rec.product_id.catch_weigth_ok and rec.product_id.average_cw_qty != 0:
                if rec.cw_uom_id == rec.product_uom:
                    rec.cw_demand = rec.product_uom_qty
                else:
                    rec.product_uom_qty = rec.cw_demand / rec.product_id.average_cw_qty

    def _cal_cw_demand(self):
        """Calculating cw demand,cw uom, cw reserved and cw done"""
        for rec in self:
            rec.update(
                {
                    'cw_demand': rec.product_uom_qty * rec.product_id.average_cw_qty,
                    'cw_uom_id': rec.product_id.cw_uom_id,
                    'cw_done': rec.quantity * rec.product_id.average_cw_qty,
                    'cw_reserved': rec.product_uom_qty * rec.product_id.average_cw_qty,
                })
