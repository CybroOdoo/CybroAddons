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


class InventoryOverStockDataReport(models.TransientModel):
    """This model is for creating a wizard for viewing the report data"""
    _name = "inventory.over.stock.data.report"
    _description = "Inventory Over Stock Data Report"

    product_id = fields.Many2one("product.product",
                                 string="Product", help="Select the Product")
    category_id = fields.Many2one("product.category",
                                  string="Category",
                                  help="Select the Product Category")
    company_id = fields.Many2one("res.company",
                                 string="Company", help="Select the Company")
    warehouse_id = fields.Many2one("stock.warehouse",
                                   string="Warehouse",
                                   help="Select the Warehouse")
    virtual_stock = fields.Float(string="Forecasted QTY",
                                 help="Forecasted quantity of stock")
    sales = fields.Float(string="Sales",
                         help="Total quantity or value of stock sold")
    ads = fields.Float(string="ADS", help="Average Daily Sales")
    demanded_quantity = fields.Float(string="Demanded QTY",
                                     help="Quantity Demanded")
    in_stock_days = fields.Float(string="Coverage Days",
                                 help="Number of days the inventory was in stock.")
    over_stock_qty = fields.Float(
        string="Over Stock QTY",
        help="Quantity of stock that exceeds the optimal or desired stock level")
    over_stock_qty_percentage = fields.Float(
        string="Over Stock QTY(%)",
        help="Percentage of quantity of stock that exceeds the optimal or"
             " desired stock level")
    over_stock_value = fields.Float(
        string="Over Stock Value",
        help="Value of stock that exceeds the optimal or desired stock level")
    over_stock_value_percentage = fields.Float(
        string="Over Stock Value(%)",
        help="Percentage of value of stock that exceeds the optimal or "
             "desired stock level")
    turnover_ratio = fields.Float(string="Turnover Ratio",
                                  help="The frequency at which stock is sold and"
                                       " replaced during a specific period")
    fsn_classification = fields.Char(
        string="FSN Classification",
        help="Classification which categorizes items based on their consumption"
             " or movement rate.")
    po_date = fields.Datetime(string="Last PO Date",
                              help="Date of last purchase")
    po_qty = fields.Float(string="Last PO QTY",
                          help="Last purchased quantity")
    po_price_total = fields.Float(string="Last PO Price",
                                  help="Total Price of last purchase")
    po_currency_id = fields.Many2one("res.currency",
                                     string="Currency",
                                     help='Currency of purchase')
    po_partner_id = fields.Many2one("res.partner",
                                    string="Partner", help="Partner of purchase")
    data_id = fields.Many2one('inventory.over.stock.report',
                              string="Over Stock Data",
                              help="Corresponding stock data")
