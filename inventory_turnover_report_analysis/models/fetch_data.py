# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class FetchData(models.Model):
    """New model to display the records in a tree view"""
    _name = "fetch.data"
    _description = "Fetch Data"

    company_id = fields.Many2one('res.company', string="Company",
                                 help="These are the selected companies from "
                                      "the wizard.")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse",
                                   help="These are the selected warehouses "
                                        "from the wizard")
    product_id = fields.Many2one('product.product', string="Product",
                                 help="Selected all products are listed below.")
    category_id = fields.Many2one('product.category', string="Product category",
                                  help="Product category of current product")
    opening_stock = fields.Float(string="Opening Stock",
                                 help="Opening stock: Value of stock at "
                                      "the beginning of an accounting period")
    closing_stock = fields.Float(string="Closing Stock",
                                 help="Closing Stock: Value of stock at the "
                                      "end of an accounting period.")
    average_stock = fields.Float(string="Average Stock",
                                 help="Average stock: Average of opening stock "
                                      "and closing stock")
    sale_count = fields.Float(string="Sales Count",
                              help="Sales count: Total number of product sale")
    purchase_count = fields.Float(string="Purchase Count",
                                  help="Purchase count: Total number of "
                                       "product purchased")
    turnover_ratio = fields.Float(string="Turnover Ratio",
                                  help="Turnover ratio: It is calculated as "
                                       "'cost of goods sold/average stock'")
