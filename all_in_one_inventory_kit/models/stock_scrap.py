# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Surya Gayathry TA (odoo@cybrosys.com)
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


class StockScrap(models.Model):
    """inherits Stock Scrap"""
    _inherit = 'stock.scrap'

    cw_qty = fields.Float(string='CW-Qty', digits=(16, 4),
                          compute='_compute_cw_qty',
                          store=True,
                          help="Catch weight quantity")
    cw_category_id = fields.Many2one('uom.uom',
                                     domain="[('relative_uom_id', '=', False)]",
                                     help="Category of the scrap",
                                     default=lambda self:
                                     self.env.ref('uom.product_uom_gram'))
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                help="Catch weight unit of measure",
                                related='product_id.product_tmpl_id.cw_uom_id')
    toggle_cw = fields.Boolean(
        string='is_cw_product',
        related='product_id.product_tmpl_id.catch_weight_ok',
        help="Is cw stock")

    @api.depends('product_id', 'scrap_qty')
    def _compute_cw_qty(self):
        """computing the qty"""
        for record in self:
            record.cw_qty = 0
            if (record.product_id.catch_weight_ok and
                    record.product_id.average_cw_qty != 0):
                record.cw_qty = (record.product_id.average_cw_qty
                                 * record.scrap_qty)
