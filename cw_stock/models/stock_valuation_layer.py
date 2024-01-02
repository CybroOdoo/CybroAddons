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


class StockValuationLayer(models.Model):
    """Inherit Stock Valuation Layer for Adding Catch Weight fields and
     functions"""
    _inherit = 'stock.valuation.layer'

    cw_qty_done = fields.Float(string='CW-Qty Done', help="Catch weight of done"
                                                          " quantity",
                               compute='_compute_cw_qty_done', digits=(16, 4))
    category_id = fields.Many2one('uom.category', string="Category",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'),
                                  help="Category of catch weight UoM")
    cw_uom_id = fields.Many2one('uom.uom',
                                related='product_id.cw_uom_id',
                                string='CW-Uom',
                                help="Catch weight unit od measure",
                                domain="[('category_id', '=', category_id)]",
                                )
    cw_hide = fields.Boolean(related='product_id.catch_weight_ok',
                             string='CW Product',
                             help="True for catch weight products")

    @api.depends('product_id', 'quantity')
    def _compute_cw_qty_done(self):
        """Calculating cw qty done"""
        for rec in self:
            rec.cw_qty_done = rec.quantity * rec.product_id.average_cw_qty if \
                rec.product_id.catch_weight_ok else 0
