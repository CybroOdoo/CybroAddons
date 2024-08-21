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


class InventoryFsnXyzDataReport(models.TransientModel):
    """This model is for creating a wizard for viewing the report data"""
    _name = "inventory.fsn.xyz.data.report"
    _description = "Inventory FSN-XYZ Data Report"

    product_id = fields.Many2one("product.product", string="Product")
    category_id = fields.Many2one("product.category", string="Category")
    company_id = fields.Many2one("res.company", string="Company")
    average_stock = fields.Float(string="Average Stock")
    sales = fields.Float(string="Sales")
    turnover_ratio = fields.Float(string="Turnover Ratio")
    current_stock = fields.Float(string="Current Stock")
    stock_value = fields.Float(string="Stock Value")
    fsn_classification = fields.Char(string="FSN Classification")
    xyz_classification = fields.Char(string="XYZ Classification")
    combined_classification = fields.Char(string="FSN-XYZ Classification")
    data_id = fields.Many2one('inventory.fsn.xyz.report', string="FSN-XYZ Data")
