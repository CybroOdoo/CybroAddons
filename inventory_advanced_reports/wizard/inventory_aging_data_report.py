# -*- coding: utf-8 -*-
###############################################################################
#
#  Cybrosys Technologies Pvt. Ltd.
#
#  Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#  Author: Jumana Haseen (odoo@cybrosys.com)
#
#  You can modify it under the terms of the GNU LESSER
#  GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#  You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#  (LGPL v3) along with this program.
#  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class InventoryAgingDataReport(models.TransientModel):
    """This model is for creating a wizard for viewing the report data"""
    _name = "inventory.aging.data.report"
    _description = "Inventory Aging Data Report"

    product_id = fields.Many2one("product.product",
                                 string="Product",
                                 help="Name of Product")
    category_id = fields.Many2one("product.category",
                                  string="Category", help="Product Category")
    company_id = fields.Many2one("res.company", string="Company",
                                 help="Select the Company")
    qty_available = fields.Float(string="Current Stock",
                                 help="On hand quantity of product")
    current_value = fields.Float(string="Current Value",
                                 help="Current value of Stock")
    stock_percentage = fields.Float(string="Stock Qty(%)",
                                    help="Percentage of current stock")
    stock_value_percentage = fields.Float(string="Stock Value(%)",
                                          help="Value of current stock")
    days_since_receipt = fields.Integer(
        string="Oldest Stock Age",
        help="Number of days since the receipt of the oldest stock item")
    prev_qty_available = fields.Float(
        string="Oldest Qty",
        help="Quantity of the oldest stock available.")
    prev_value = fields.Float(
        string="Oldest Stock Value",
        help="Total monetary value of oldest stock.")
    data_id = fields.Many2one('inventory.aging.report',
                              string="Aging Data",
                              help="Reference of corresponding Aging data.")
