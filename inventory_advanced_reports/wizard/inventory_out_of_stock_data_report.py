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


class InventoryOutOfStockDataReport(models.TransientModel):
    """This model is for creating a wizard for viewing the report data"""
    _name = "inventory.out.of.stock.data.report"
    _description = "Inventory Out Of Stock Data Report"

    product_id = fields.Many2one("product.product",
                                 string="Product",
                                 help="Select the Product.")
    category_id = fields.Many2one("product.category",
                                  string="Category",
                                  help="Select the Product Category.")
    company_id = fields.Many2one("res.company", string="Company",
                                 help="Select the Company.")
    warehouse_id = fields.Many2one("stock.warehouse",
                                   string="Warehouse",
                                   help="Select the Warehouse.")
    virtual_stock = fields.Float(string="Forecasted QTY",
                                 help="Forecasted quantity of stock")
    sales = fields.Float(string="Sales",
                         help="Total quantity or value of stock sold")
    ads = fields.Float(string="ADS", help="Average Daily Sales")
    demanded_quantity = fields.Float(string="Demanded QTY",
                                     help="Quantity demanded")
    in_stock_days = fields.Float(
        string="In Stock Days",
        help="Number of days the inventory was in stock.")
    out_of_stock_days = fields.Float(
        string="Out Of Stock Days",
        help="Number of days the inventory was unavailable or out of stock.")
    out_of_stock_ratio = fields.Float(
        string="Out Of Stock Ratio",
        help="Proportion of out-of-stock days relative to the total"
             " days in the period")
    cost = fields.Float(string="Cost Price", help="Cost of the stock")
    out_of_stock_qty = fields.Float(string="Out Of Stock QTY",
                                    help="Total quantity of out of stock")
    out_of_stock_qty_percentage = fields.Float(
        string="Out Of Stock QTY(%)",
        help="Percentage of out of stock quantity")
    out_of_stock_value = fields.Float(
        string="Out Of Stock Value(%)",
        help="Total value of out of stock quantity")
    turnover_ratio = fields.Float(
        string="Turnover Ratio",
        help="The frequency at which stock is sold and replaced during a"
             " specific period.")
    fsn_classification = fields.Char(
        string="FSN Classification",
        help="Classification which categorizes items based on their consumption"
             " or movement rate.")
    data_id = fields.Many2one('inventory.out.of.stock.report',
                              string="Out Of Stock Data",
                              help="corresponding FSN data")
