# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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


class PurchaseOrderLine(models.Model):
    """Inherits the model and added required fields"""
    _inherit = 'purchase.order.line'

    cw_qty = fields.Float(string='CW-Qty', digits=(16, 4),
                          help="Catch weight quantity.")
    category_id = fields.Many2one('uom.category',
                                  help="Unit of measure "
                                       "category of the product.",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                help="Catch weight unit of measure.",
                                domain="[('category_id', '=', category_id)]")
    cw_received = fields.Float(string='CW-Received', readonly=True,
                               compute='_compute_cw_invoiced_cw_received',
                               digits=(16, 4),
                               help="CW received quantity.")
    cw_invoiced = fields.Float(string='CW-Invoiced', readonly=True,
                               compute='_compute_cw_invoiced_cw_received',
                               digits=(16, 4),
                               help="CW invoiced quantity after invoice "
                                    "has created.")

    @api.onchange('product_id', 'product_qty')
    def _onchange_product_id_product_qty(self):
        """Change product and product quantity
        Calculating the cw unit of measure and cw quantity"""
        for rec in self:
            if rec.product_id.catch_weigth_ok:
                rec.price_unit = rec.product_id.list_price
                rec.cw_uom_id = rec.product_id.cw_uom_id.id
                if rec.cw_uom_id == rec.product_uom:
                    rec.product_qty = rec.cw_qty
                else:
                    rec.cw_qty = rec.product_qty * rec.product_id.average_cw_qty

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Change the cw qty"""
        for rec in self:
            if rec.product_id.catch_weigth_ok and rec.product_id.average_cw_qty != 0:
                if rec.cw_uom_id == rec.product_uom:
                    rec.product_qty = rec.cw_qty
                else:
                    rec.product_qty = rec.cw_qty / rec.product_id.average_cw_qty

    def _compute_cw_invoiced_cw_received(self):
        """Calculating cw received and invoiced qty
        Calculating uom and price"""
        for rec in self:
            rec.update({
                'cw_received': rec.qty_received * rec.product_id.average_cw_qty,
                'price_unit': rec.product_id.list_price,
                'cw_uom_id': rec.product_id.cw_uom_id,
                'cw_invoiced': rec.qty_invoiced * rec.product_id.average_cw_qty
            })
