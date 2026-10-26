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
from odoo import fields, models


class SaleOrderLine(models.Model):
    """
    Inheriting the 'sale.order.line' model add the product_design field
    """
    _inherit = 'sale.order.line'

    product_design = fields.Binary(
        string="Product Design",
        help="Customized design image applied to this product line.",
    )
    is_customized_product = fields.Boolean(
        string="Customized Product",
        help="Indicates whether this order line contains a customized product.",
        default=False,
    )
