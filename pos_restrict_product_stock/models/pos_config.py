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


class PosConfig(models.Model):
    """Inherited pos configuration setting for adding fields for
    restricting out-of-stock products."""
    _inherit = 'pos.config'

    is_display_stock = fields.Boolean(
        string="Display Stock in POS",
        help="Enable if you want to show quantity of products",
    )
    is_restrict_product = fields.Boolean(
        string="Restrict Out-of-Stock Products in POS",
        help="Enable to restrict out-of-stock products in POS",
    )
    stock_type = fields.Selection(
        [
            ('qty_on_hand', 'Qty on Hand'),
            ('virtual_qty', 'Virtual Qty'),
            ('both', 'Both'),
        ],
        required=True,
        default='qty_on_hand',
        string="Stock Type",
        help="Stock quantity type to display and restrict in POS",
    )
