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


class InventoryFsnXyzDataReport(models.TransientModel):
    """This model is for creating a wizard for viewing the report data"""
    _name = "inventory.fsn.xyz.data.report"
    _description = "Inventory FSN-XYZ Data Report"

    product_id = fields.Many2one("product.product",
                                 string="Product", help="Select the Product")
    category_id = fields.Many2one("product.category",
                                  string="Category",
                                  help="Select the Product Category")
    company_id = fields.Many2one("res.company",
                                 string="Company",
                                 help="Select the Company")
    average_stock = fields.Float(string="Average Stock",
                                 help="Average quantity of Stock")
    sales = fields.Float(string="Sales",
                         help="Total quantity or value of stock sold")
    turnover_ratio = fields.Float(
        string="Turnover Ratio",
        help="The frequency at which stock is sold and replaced during a"
             " specific period.")
    current_stock = fields.Float(string="Current Stock",
                                 help="Quantity of Stock available currently")
    stock_value = fields.Float(string="Stock Value",
                               help="Value of Stock available currently")
    fsn_classification = fields.Char(
        string="FSN Classification",
        help="FSN classification of the stock, which categorizes items based on"
             " their consumption or movement rate.")
    xyz_classification = fields.Char(
        string="XYZ Classification",
        help="Categorizing inventory items based on their variability in"
             " consumption.")
    combined_classification = fields.Char(
        string="FSN-XYZ Classification",
        help="The classification merging FSN and XYZ categorizations."                                  )
    data_id = fields.Many2one('inventory.fsn.xyz.report',
                              string="FSN-XYZ Data",
                              help="corresponding FSN-XYZ data")
