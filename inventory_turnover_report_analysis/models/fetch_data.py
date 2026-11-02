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


class FetchData(models.Model):
    """Create a new model to show the records in list view."""
    _name = "fetch.data"
    _description = "Fetch Data"

    company_id = fields.Many2one(
        'res.company',
        help="The company selected in the wizard.")
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        help="The warehouse selected in the wizard.")
    product_id = fields.Many2one(
        'product.product',
        help="The products selected in the wizard.")
    category_id = fields.Many2one(
        'product.category', string="Product Category",
        help="Product category of the current product.")
    opening_stock = fields.Float(
        help="Opening stock: quantity in stock at the beginning of the "
             "period.")
    closing_stock = fields.Float(
        help="Closing stock: quantity in stock at the end of the period.")
    average_stock = fields.Float(
        help="Average stock: average of the opening stock and the closing "
             "stock.")
    sale_count = fields.Float(
        string="Sales Count",
        help="Sales count: total number of units sold.")
    purchase_count = fields.Float(
        help="Purchase count: total number of units purchased.")
    turnover_ratio = fields.Float(
        help="Turnover ratio: calculated as the cost of goods sold divided "
             "by the average stock.")
