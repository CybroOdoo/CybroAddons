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
