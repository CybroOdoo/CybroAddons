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


class SaleOrderLine(models.Model):
    """Inherit sale order line to include catch weight fields and functions"""
    _inherit = 'sale.order.line'

    cw_qty = fields.Float(string='CW-Qty', digits=(16, 4),
                          help="Catch weight quantity")
    category_id = fields.Many2one('uom.category', string="Category",
                                  help="Category of the Product",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom',
                                related='product_id.cw_uom_id',
                                string='CW-Uom',
                                domain="[('category_id', '=', category_id)]",
                                help="Catch weight unit of measure")
    cw_delivered = fields.Float(string='CW-Delivered', help="Catch Weight of "
                                                            "Delivered Product",
                                compute='_compute_cw_delivered', digits=(16, 4))
    cw_invoiced = fields.Float(string='CW-Invoiced', help="Catch Weight of "
                                                          "Delivered Product",
                               digits=(16, 4),
                               compute='_compute_cw_delivered')
    is_cw_product = fields.Boolean(related='product_id.catch_weight_ok',
                                   string='Is CW Product',
                                   help="True for Catch Weight product"
                                   )

    def _compute_cw_delivered(self):
        """Method for calculating cw_delivered and cw_invoiced"""
        for rec in self:
            rec.update({
                'cw_delivered': rec.qty_delivered * rec.product_id.
                average_cw_qty,
                'cw_invoiced': rec.qty_invoiced * rec.product_id.
                average_cw_qty
            })

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id(self):
        """Method for updating the cw_qty when product_id or product_uom_qty
        changes"""
        if self.product_id.catch_weight_ok:
            self.cw_qty = self.product_uom_qty * self.product_id.average_cw_qty

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Method for calculating product qty based on cw qty f cw quantity
        changed"""
        if self.product_id.catch_weight_ok and self.product_id. \
                average_cw_qty != 0:
            self.product_uom_qty = self.cw_qty / self.product_id. \
                average_cw_qty
