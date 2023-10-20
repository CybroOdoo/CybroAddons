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


class PurchaseOrderLine(models.Model):
    """Inherits Purchase Order line for adding catch weight fields and
    functions"""
    _inherit = 'purchase.order.line'

    cw_qty = fields.Float(string='CW Quantity', digits=(16, 4),
                          help="Catch weight quantity")
    category_id = fields.Many2one('uom.category', string="Category",
                                  help="Category of the Product",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                related='product_id.cw_uom_id',
                                help="Catch weight unit of measure",
                                domain="[('category_id', '=', category_id)]")
    cw_invoiced = fields.Float(string='CW-Invoiced', readonly=True,
                               compute='_compute_cw_invoiced',
                               help="True for catch weight products",
                               digits=(16, 4))
    cw_received = fields.Float(string='CW-Received', readonly=True,
                               compute='_compute_cw_invoiced',
                               digits=(16, 4), help='Catch weight received')
    toggle_cw = fields.Boolean(
        related='product_id.product_tmpl_id.catch_weight_ok',
        string='is_cw_product',
        help="True for catch weight products")

    def _compute_cw_invoiced(self):
        """Method for calculating cw_received, cw_invoiced, price_unit and
        cw_uom_id"""
        for rec in self:
            rec.update({
                'cw_received': rec.qty_received * rec.product_id.average_cw_qty,
                'price_unit': rec.product_id.list_price,
                'cw_uom_id': rec.product_id.cw_uom_id,
                'cw_invoiced': rec.qty_invoiced * rec.product_id.average_cw_qty
            })

    @api.onchange('product_id', 'product_qty')
    def _onchange_product_id(self):
        """Method for calculating the cw unit of measure and cw quantity"""
        for rec in self:
            if rec.product_id.catch_weight_ok:
                if rec.cw_uom_id == rec.product_uom:
                    rec.product_qty = rec.cw_qty
                else:
                    rec.cw_qty = rec.product_qty * rec.product_id.average_cw_qty

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Method for calculating the product quantity"""
        for rec in self:
            if rec.product_id.catch_weight_ok and \
                    rec.product_id.average_cw_qty != 0:
                if rec.cw_uom_id == rec.product_uom:
                    rec.product_qty = rec.cw_qty
                else:
                    rec.product_qty = rec.cw_qty / rec.product_id.average_cw_qty
