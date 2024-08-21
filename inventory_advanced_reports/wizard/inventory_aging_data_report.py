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


class InventoryAgingDataReport(models.TransientModel):
    """This model is for creating a wizard for viewing the report data"""
    _name = "inventory.aging.data.report"
    _description = "Inventory Aging Data Report"

    product_id = fields.Many2one("product.product", string="Product")
    category_id = fields.Many2one("product.category", string="Category")
    company_id = fields.Many2one("res.company", string="Company")
    qty_available = fields.Float(string="Current Stock")
    current_value = fields.Float(string="Current Value")
    stock_percentage = fields.Float(string="Stock Qty(%)")
    stock_value_percentage = fields.Float(string="Stock Value(%)")
    days_since_receipt = fields.Integer(string="Oldest Stock Age")
    prev_qty_available = fields.Float(string="Oldest Qty")
    prev_value = fields.Float(string="Oldest Stock Value")
    data_id = fields.Many2one('inventory.aging.report', string="Aging Data")
