# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    apply_cw = fields.Boolean()
    category_id = fields.Many2one('uom.category',
                                  default=lambda self: self.env.ref(
                                      'uom.product_uom_categ_kgm'))
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom', stored=True,
                                help="Catch weight unit of measure",
                                domain="[('category_id', '=', category_id)]")
    catch_weigth_ok = fields.Boolean(default=False,
                                     string="Catch Weight Product")
    average_cw_qty = fields.Float(string='Catch Weight', digits=(16, 4),
                                  help="Catch weight quantity")

    @api.onchange('cw_uom_id', 'uom_id')
    def compute_weight(self):
        """Calculating cw qty if uom and cw uom category is same"""
        if self.uom_id.category_id == self.cw_uom_id.category_id:
            self.average_cw_qty = self.cw_uom_id.factor / self.uom_id.factor
        else:
            self.average_cw_qty = 1.00
