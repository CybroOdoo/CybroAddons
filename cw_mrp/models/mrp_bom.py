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


class MrpBom(models.Model):
    """Inherits mrp.bom for adding catch weight fields and functions"""
    _inherit = 'mrp.bom'

    cw_qty = fields.Float(related='product_tmpl_id.average_cw_qty',
                          string='CW-Qty', digits=(16, 4),
                          help="Catch weight quantity", readonly=False)
    category_id = fields.Many2one('uom.category', string="Category",
                                  help="Category of the Product",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom',
                                related='product_tmpl_id.cw_uom_id',
                                string='CW-Uom',
                                help="Catch weight unit of measure",
                                domain="[('category_id', '=', category_id)]",
                                store=True)
    toggle_cw = fields.Boolean(related='product_tmpl_id.catch_weight_ok',
                               string='is_cw_product',
                               help="True for catch weight products")

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Calculates value of product_qty"""
        if self.toggle_cw and self.product_tmpl_id.average_cw_qty != 0:
            self.product_qty = self.cw_qty / self.product_tmpl_id.average_cw_qty

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        """Method for calculating the value of cw_qty"""
        if self.toggle_cw:
            self.cw_qty = self.product_tmpl_id.average_cw_qty * self.product_qty
