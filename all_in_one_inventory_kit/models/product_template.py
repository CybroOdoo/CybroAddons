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
################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """inherits product.template"""
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', string='Brand',
                               help="Product Brand")
    cw_category_id = fields.Many2one('uom.uom',
                                     domain="[('relative_uom_id', '=', False)]",
                                     default=lambda self: self.env.ref(
                                         'uom.product_uom_gram'),
                                     help="Unit of measure categories")
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                store=True,
                                help="Catch weight unit of measure",
                                domain="[('id', 'child_of', cw_category_id)]")
    catch_weight_ok = fields.Boolean(default=False,
                                     string="Catch Weight Product",
                                     help="Is catch weight enabled")
    average_cw_qty = fields.Float(string='Catch Weight', digits=(16, 4),
                                  help="Catch weight quantity")
    product_stock_location_ids = fields.One2many(
        'stock.quant',
        'product_tmpl_id',
        string='Stock By Location',
        help="Product stock locations"
    )

    def action_get_wo_description(self):
        """Method for print pdf report """
        return self.env.ref(
            'all_in_one_inventory_kit.product_product_report_action') \
            .report_action(self, data='')

    @api.onchange('cw_uom_id', 'uom_id')
    def _onchange_cw_uom_id(self):
        """Calculating cw qty if uom and cw uom category is same"""
        if self.uom_id and self.cw_uom_id and self.uom_id._has_common_reference(self.cw_uom_id):
            self.average_cw_qty = self.uom_id.factor / self.cw_uom_id.factor
        else:
            self.average_cw_qty = 1.00
