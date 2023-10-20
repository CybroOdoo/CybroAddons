# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    """Inherits Account Move Line for adding more fields and functions
    related to Catch Weight"""
    _inherit = 'account.move.line'

    cw_qty = fields.Float(string='CW-Qty', compute='_compute_cw_qty',
                          help="Catch weight quantity", readonly=False,
                          digits=(16, 4)
                          )
    category_id = fields.Many2one('uom.category', string="Category",
                                  help="Category of the product",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom', related='product_id.cw_uom_id',
                                string='Catch Weight UOM', readonly=False,
                                domain="[('category_id', '=', category_id)]",
                                help="Catch weight unit of measure",
                                )
    cw_hide = fields.Boolean(string='CW-Hide',
                             related='product_id.catch_weight_ok',
                             help="For hiding the catch weight fields depending"
                                  " on this field")

    @api.depends('product_id')
    def _compute_cw_qty(self):
        """Compute CW quantity of the product"""
        for rec in self:
            rec.update({'cw_qty': rec.product_id.average_cw_qty * rec.quantity})

    @api.onchange('product_id', 'quantity')
    def _onchange_product_id(self):
        """Calculates cw qty and cw uom"""
        for rec in self:
            if rec.product_id.catch_weight_ok:
                rec.cw_qty = rec.product_id.average_cw_qty * rec.quantity
        return super()._onchange_product_id()

    @api.onchange('cw_qty')
    def _onchange_cw_cty(self):
        """Calculates quantity of the product based on catch weight quantity"""
        for rec in self:
            if rec.product_id.catch_weight_ok and \
                    rec.product_id.average_cw_qty != 0:
                rec.quantity = rec.cw_qty / rec.product_id.average_cw_qty

    @api.onchange('product_uom_id', 'cw_uom_id')
    def _onchange_product_uom_id(self):
        """Calculates cw_qty of the product"""
        for rec in self:
            if rec.product_id.catch_weight_ok and rec.cw_uom_id and \
                    rec.product_uom_id.category_id == rec.cw_uom_id.category_id:
                rec.cw_qty = rec.cw_uom_id.factor / rec.product_uom_id.factor
