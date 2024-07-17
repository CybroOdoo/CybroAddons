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


class StockScrap(models.Model):
    """inherits Stock Scrap"""
    _inherit = 'stock.scrap'

    cw_qty = fields.Float(string='CW-Qty', digits=(16, 4),
                          compute='_compute_cw_qty',
                          help="Catch weight quantity")
    category_id = fields.Many2one('uom.category',
                                  help="Category of the scrap",
                                  default=lambda self:
                                  self.env.ref('uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                help="Catch weight unit of measure",
                                related='product_id.product_tmpl_id.cw_uom_id')
    toggle_cw = fields.Boolean(
        string='is_cw_product',
        related='product_id.product_tmpl_id.catch_weight_ok',
        help="Is cw stock")

    @api.depends('product_id')
    def _compute_cw_qty(self):
        """computing the qty"""
        self.cw_qty = 0
        if self.product_id.catch_weight_ok and self.product_id.average_cw_qty \
                != 0:
            self.cw_qty = self.product_id.average_cw_qty * self.scrap_qty
