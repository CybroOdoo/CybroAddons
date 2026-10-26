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


class PosCrossSellingLine(models.Model):
    """Pos Cross-Selling Products Line"""
    _name = 'pos.cross.selling.line'
    _description = 'POS Cross-Selling Product Line'

    product_id = fields.Many2one('product.product',
                                 domain=[('available_in_pos', '=', True)],
                                 required=True, string='Product Name',
                                 help="Product details")
    active = fields.Boolean(string='Active',
                            help="To check the cross selling is active or not",
                            default=True)
    pos_cross_product_id = fields.Many2one('pos.cross.selling',
                                           string='POS Cross Products',
                                           help="POS cross-selling products")
