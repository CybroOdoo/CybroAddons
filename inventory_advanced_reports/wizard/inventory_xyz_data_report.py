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


class InventoryXyzDataReport(models.TransientModel):
    """This model is for creating a wizard for viewing the report data"""
    _name = "inventory.xyz.data.report"
    _description = "Inventory XYZ Data Report"

    product_id = fields.Many2one("product.product", string="Product")
    category_id = fields.Many2one("product.category", string="Category")
    company_id = fields.Many2one("res.company", string="Company")
    current_stock = fields.Float(string="Current Stock")
    stock_value = fields.Float(string="Stock Value")
    stock_percentage = fields.Float(string="Stock Value(%)")
    cumulative_stock_percentage = fields.Float(string="CUMULATIVE STOCK( %)")
    xyz_classification = fields.Char(string="XYZ CLASSIFICATION")
    data_id = fields.Many2one('inventory.xyz.report', string="XYZ Data")
