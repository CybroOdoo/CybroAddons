# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class PricelistLine(models.TransientModel):
    _name = 'pricelist.line'
    _rec_name = 'wizard_id'
    _description = 'Pricelist Lines'

    wizard_id = fields.Many2one('pricelist.product',
                                string="Price List Selection",
                                help="Price List Selection")
    pricelist_id = fields.Many2one('product.pricelist',
                                   string="PriceList",
                                   help="Price lists that can be applied for "
                                        "the order line.")
    product_id = fields.Many2one('product.product',
                                 string="Product",
                                 help="Order line Product")
    unit_price = fields.Float(string="Unit Price",
                              help="Price of the product per unit")
    unit_cost = fields.Float(string='Unit Cost',
                             help="Cost of the product per unit")
    margin = fields.Float(compute='_compute_margin', string="Margin %",
                          help="calculated by ((unit price - unit cost) "
                               "unit cost)* 100")
    uom_id = fields.Many2one('uom.uom', string="UOM", help="Unit Of Measure")

    @api.depends('unit_price', 'unit_cost')
    def _compute_margin(self):
        """ This function will compute the margin for the product when the
        price list applied.
        It is calculated by ((unit price - unit cost)/ unit cost)* 100"""
        for rec in self:
            rec.margin = 100
            if rec.unit_cost:
                rec.margin = ((rec.unit_price-rec.unit_cost)/rec.unit_cost)*100

    def apply_pricelist(self):
        """This function will apply the selected pricelist to the order
         line."""
        for rec in self:
            rec.wizard_id.order_line_id.update({
                'applied_pricelist_id': rec.pricelist_id,
            })
            rec.wizard_id.order_line_id.update({
                'price_unit': rec.unit_price,
            })
