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
from odoo import fields, models


class PricelistProduct(models.TransientModel):
    """ New transient model for the price list wizard """
    _name = 'pricelist.product'
    _rec_name = 'order_line_id'
    _description = 'Price list product'

    order_line_id = fields.Many2one('sale.order.line',
                                    help="Order line of the selected order")
    line_ids = fields.One2many('pricelist.line', 'wizard_id',
                               string="Price lists", help="Pricelist lines")
