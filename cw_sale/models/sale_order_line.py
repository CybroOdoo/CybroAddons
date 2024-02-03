# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra K (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """ Inherited the model Sale Order Line for adding the catch
    weight sale fields."""
    _inherit = 'sale.order.line'

    cw_qty = fields.Float(string='CW-Qty', digits=(16, 4),
                          help="Catch weight quantity")
    category_id = fields.Many2one('uom.category', string='Category',
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'),
                                  help='The Uom Category.')
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                domain="[('category_id', '=', category_id)]",
                                help="Catch weight unit of measure")
    cw_delivered = fields.Float(string='CW-Delivered',
                                compute='_compute_cal_cw', digits=(16, 4),
                                help='Catch weight delivered amount')
    cw_invoiced = fields.Float(string='CW-Invoiced',
                               digits=(16, 4),
                               compute='_compute_cal_cw',
                               help='Catch weight invoiced amount')
    is_cw_product = fields.Boolean(string='Is CW Product',
                                   compute="_compute_is_cw_product",
                                   help='Catch weight product')

    @api.depends('product_id')
    def _compute_is_cw_product(self):
        """ To hide the field is_cw_product."""
        for rec in self:
            rec.is_cw_product = bool(rec.product_id.catch_weight_ok)

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id(self):
        """Change product and product quantity Calculating the cw unit of measure ,
        cw quantity and price"""
        for rec in self:
            if rec.product_id.catch_weight_ok:
                rec.price_unit = rec.product_id.list_price
                rec.cw_uom_id = rec.product_id.cw_uom_id.id
                if rec.cw_uom_id == rec.product_uom:
                    rec.cw_qty = rec.product_uom_qty
                else:
                    rec.cw_qty = rec.product_uom_qty * rec.product_id.average_cw_qty

    @api.onchange('cw_qty')
    def _onchange_cw_cty(self):
        """Calculating product qty based on cw qty"""
        for rec in self:
            if rec.product_id.catch_weight_ok and rec.product_id.average_cw_qty != 0:
                if rec.cw_uom_id == rec.product_uom:
                    rec.product_uom_qty = rec.cw_qty
                else:
                    rec.product_uom_qty = rec.cw_qty / rec.product_id.average_cw_qty

    def _compute_cal_cw(self):
        """Calculating cw delivered and invoiced qty
                Calculating cw uom """
        for rec in self:
            rec.update({
                'cw_delivered': rec.qty_delivered * rec.product_id.average_cw_qty,
                'cw_uom_id': rec.product_id.cw_uom_id,
                'cw_invoiced': rec.qty_invoiced * rec.product_id.average_cw_qty
            })
