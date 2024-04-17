# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anjhana A K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ForecastReport(models.TransientModel):
    """A Transient model for the inventory forecast analysis report"""

    _name = "forecast.report"
    _description = "Stock Forecast Analysis Report"
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product",
                                 string="Product", help="Product")
    product_category_id = fields.Many2one(
        "product.category", string="Category",
        help="Category of the product")
    product_brand_id = fields.Many2one(
        "product.brand", string="Brand",
        help="Brand of the product")
    supplier_id = fields.Many2one(
        "product.supplierinfo", string="Supplier",
        help="Supplier of the product")
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        related="supplier_id.partner_id",
        store=True,
        help="Primary supplier of the product",)
    location_id = fields.Many2one(
        "stock.location", string="Location",
        help="Product Location")
    sold = fields.Float(string="Sold Qty", help="The qty that is already sold")
    on_hand = fields.Float(string="On Hand Qty",
                           help="On-hand qty of the product")
    forecast = fields.Float(
        string="Forecasted Qty", help="Forecasted qty of the product")
    pending = fields.Float(string="Pending Qty", help="Pending quantity")
    minimum = fields.Float(string="Minimum Qty", help="Minimum quantity")
    suggested = fields.Float(string="Suggested Qty", help="Suggested quantity")
