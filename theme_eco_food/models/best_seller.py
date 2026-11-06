# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Best seller snippet model."""

from odoo import fields, models


class BestSeller(models.Model):  # pylint: disable=abstract-method
    """Configure the products displayed in the best-seller snippet."""

    _name = "best.seller"
    _description = "Best Seller"

    name = fields.Char(required=True, help="Name of the category.")
    product_tmpl_ids = fields.Many2many(
        "product.template",
        domain="[('sale_ok', '=', True), ('is_published', '=', True)]",
        string="Best-Selling Products",
        help="Choose best selling products",
    )
