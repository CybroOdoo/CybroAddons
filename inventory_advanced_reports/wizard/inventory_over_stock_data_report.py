# -*- coding: utf-8 -*-
###############################################################################
#
#  Cybrosys Technologies Pvt. Ltd.
#
#  Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#  Author: Anusha C (odoo@cybrosys.com)
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

    product_id = fields.Many2one("product.product", string="Product")
    category_id = fields.Many2one("product.category", string="Category")
    company_id = fields.Many2one("res.company", string="Company")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")
    virtual_stock = fields.Float(string="Forecasted QTY")
    sales = fields.Float(string="Sales")
    ads = fields.Float(string="ADS")
    demanded_quantity = fields.Float(string="Demanded QTY")
    in_stock_days = fields.Float(string="Coverage Days")
    over_stock_qty = fields.Float(string="Over Stock QTY")
    over_stock_qty_percentage = fields.Float(string="Over Stock QTY(%)")
    over_stock_value = fields.Float(string="Over Stock Value")
    over_stock_value_percentage = fields.Float(string="Over Stock Value(%)")
    turnover_ratio = fields.Float(string="Turnover Ratio")
    fsn_classification = fields.Char(string="FSN Classification")
    po_date = fields.Datetime(string="Last PO Date")
    po_qty = fields.Float(string="Last PO QTY")
    po_price_total = fields.Float(string="Last PO Price")
    po_currency_id = fields.Many2one("res.currency", string="Currency")
    po_partner_id = fields.Many2one("res.partner", string="Partner")
    data_id = fields.Many2one('inventory.over.stock.report',
                              string="Over Stock Data")
