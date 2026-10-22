# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class PricelistLine(models.TransientModel):
    """ Model for applying the price lists for sale orderline items """
    _name = 'pricelist.line'
    _rec_name = 'wizard_id'
    _description = 'Pricelist Lines'

    wizard_id = fields.Many2one('pricelist.product',
                                string="Pricelist Selection",
                                help="Pricelist Selection")
    pricelist_id = fields.Many2one('product.pricelist',
                                   help="Pricelists that can be applied to "
                                        "the order line.")
    product_id = fields.Many2one('product.product',
                                 help="Order line Product")
    unit_price = fields.Float(help="Price of the product per unit")
    unit_cost = fields.Float(help="Cost of the product per unit")
    margin = fields.Float(compute='_compute_margin', string="Margin %",
                          help="Calculated by ((unit price - unit cost) / "
                               "unit cost) * 100")
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
