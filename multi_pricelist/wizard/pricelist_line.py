# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class PricelistLine(models.TransientModel):
    """ Model for applying the price lists for sale orderline items """
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
        It is calculated by ((unit price - unit cost)/ unit cost)* 100 """
        for rec in self:
            rec.margin = 100
            if rec.unit_cost:
                rec.margin = ((rec.unit_price-rec.unit_cost)/rec.unit_cost)*100

    def apply_pricelist(self):
        """This function will apply the selected pricelist to the order line"""
        for rec in self:
            rec.wizard_id.order_line_id.update({
                'applied_pricelist_id': rec.pricelist_id,
            })
            rec.wizard_id.order_line_id.update({
                'price_unit': rec.unit_price,
            })
