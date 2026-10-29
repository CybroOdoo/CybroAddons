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


class ProductDesignColor(models.Model):
    """Model for storing design colors available to customers for customization."""
    _name = 'product.design.color'
    _description = 'Product Design Color'
    _order = 'sequence, name'

    name = fields.Char(
        string="Color Name",
        required=True,
        help="Display name for this color, e.g. 'Red', 'Navy Blue'."
    )
    color_code = fields.Char(
        required=True,
        help="Hex color code, e.g. '#FF0000'."
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
