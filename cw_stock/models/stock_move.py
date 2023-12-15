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


class StockMove(models.Model):
    """Inherit Stock Move for adding Catch Weight fields and functions"""
    _inherit = 'stock.move'

    category_id = fields.Many2one('uom.category',
                                  string="UoM Category",
                                  help="True if it is a Catch Weight Product",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom', string='CW-UoM',
                                related='product_id.product_tmpl_id.cw_uom_id',
                                help="Catch weight unit of measure",
                                domain="[('category_id', '=', category_id)]")
    cw_demand = fields.Float(string='CW-Demand', required=True,
                             digits=(16, 4), compute='_compute_cw_demand',
                             help="The catch weight of product demanded")
    cw_reserved = fields.Float(string='CW-Reserved',
                               compute='_compute_cw_demand',
                               help="Catch weight to be reserved",
                               digits=(16, 4))
    cw_done = fields.Float(string='CW-Done', digits=(16, 4),
                           help="Catch weight of done",
                           compute='_compute_cw_demand', )
    cw_hide = fields.Boolean(related='product_id.catch_weight_ok',
                             string='CW Product',
                             help="True for catch weight products.")

    def _compute_cw_demand(self):
        """Method for computing cw_demand,cw_uom, cw_reserved and cw_done"""
        for rec in self:
            rec.update(
                {
                    'cw_demand': (rec.product_uom_qty *
                                  rec.product_id.average_cw_qty),
                    'cw_done': rec.quantity_done * rec.product_id.
                    average_cw_qty,
                    'cw_reserved': rec.product_uom_qty * rec.product_id.
                    average_cw_qty,
                })

    @api.onchange('product_id', 'product_uom_qty')
    def onchange_product_id(self):
        """Method for calculating cw demand, uom_id and cw_reserved"""
        if self.product_id.catch_weight_ok:
            self.update(
                {
                    'cw_demand': (self.product_uom_qty *
                                  self.product_id.average_cw_qty),
                    'cw_uom_id': self.product_id.cw_uom_id,
                    'cw_reserved': (self.product_uom_qty *
                                    self.product_id.average_cw_qty)
                })
        return super().onchange_product_id()

    @api.onchange('cw_demand')
    def _onchange_cw_demand(self):
        """Calculates the value of product_uom_qty if cw_demand changed"""
        for rec in self:
            if rec.product_id.catch_weight_ok and \
                    rec.product_id.average_cw_qty != 0:
                rec.product_uom_qty = rec.cw_demand / \
                                      rec.product_id.average_cw_qty


class StockMoveLine(models.Model):
    """Inherits stock move line to include Catch Weight fields"""
    _inherit = 'stock.move.line'

    cw_qty_done = fields.Float(string='CW-Qty Done',
                               help="Catch Weight Done quantity",
                               compute='_compute_cw_qty_done',
                               digits=(16, 4))
    category_id = fields.Many2one('uom.category',
                                  string="UoM Category",
                                  help="Category of the Product",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom',
                                related='product_id.product_tmpl_id.cw_uom_id',
                                string='CW-UoM',
                                help="Unit of Measure of Catch Weight",
                                domain="[('category_id', '=', category_id)]",
                                )
    cw_hide = fields.Boolean(related='product_id.catch_weight_ok',
                             string='CW Product',
                             help="True for Catch Weight products")

    @api.depends('product_id', 'qty_done')
    def _compute_cw_qty_done(self):
        """Method for calculating the value of cw_qty_done for catch weight
        products"""
        for rec in self:
            rec.cw_qty_done = rec.qty_done * rec.product_id.average_cw_qty \
                if rec.product_id.catch_weight_ok else 0
