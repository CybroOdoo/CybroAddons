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


class InventoryOutOfStockDataReport(models.TransientModel):
    """This model is for creating a wizard for viewing the report data"""
    _name = "inventory.out.of.stock.data.report"
    _description = "Inventory Out Of Stock Data Report"

    product_id = fields.Many2one("product.product", string="Product")
    category_id = fields.Many2one("product.category", string="Category")
    company_id = fields.Many2one("res.company", string="Company")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")
    virtual_stock = fields.Float(string="Forecasted QTY")
    sales = fields.Float(string="Sales")
    ads = fields.Float(string="ADS")
    demanded_quantity = fields.Float(string="Demanded QTY")
    in_stock_days = fields.Float(string="In Stock Days")
    out_of_stock_days = fields.Float(string="Out Of Stock Days")
    out_of_stock_ratio = fields.Float(string="Out Of Stock Ratio")
    cost = fields.Float(string="Cost Price")
    out_of_stock_qty = fields.Float(string="Out Of Stock QTY")
    out_of_stock_qty_percentage = fields.Float(string="Out Of Stock QTY(%)")
    out_of_stock_value = fields.Float(string="Out Of Stock Value(%)")
    turnover_ratio = fields.Float(string="Turnover Ratio")
    fsn_classification = fields.Char(string="FSN Classification")
    data_id = fields.Many2one('inventory.out.of.stock.report',
                              string="Out Of Stock Data")
