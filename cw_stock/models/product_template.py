# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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


class ProductTemplate(models.Model):
    """Inherits the Product template model for adding new fields
    and functions"""
    _inherit = 'product.template'

    apply_cw = fields.Boolean(string="Is apply Cw",
                              help="Whether to apply the Cw")
    category_id = fields.Many2one('uom.category', string="Category",
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'),
                                  help="Category of the CW")
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom', stored=True,
                                help="Catch weight unit of measure",
                                domain="[('category_id', '=', category_id)]")
    catch_weigth_ok = fields.Boolean(default=False,
                                     help="Whether the weight unit is ok",
                                     string="Catch Weight Product")
    average_cw_qty = fields.Float(string='Catch Weight', digits=(16, 4),
                                  help="Catch weight quantity")

    @api.onchange('cw_uom_id', 'uom_id')
    def _onchange_cw_uom_id(self):
        """Calculating cw qty if uom and cw uom category is same"""
        if self.uom_id.category_id == self.cw_uom_id.category_id:
            self.average_cw_qty = self.cw_uom_id.factor / self.uom_id.factor
        else:
            self.average_cw_qty = 1.00
