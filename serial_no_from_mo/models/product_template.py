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


class ProductTemplate(models.Model):
    """ This model extends the base `product.template` model to add custom
    fields for specifying the number of digits and prefix for the product."""
    _inherit = 'product.template'

    mo_serial_digit = fields.Integer(
        string="Number of Digits",
        help="Specify the desired number of digits.")
    mo_serial_prefix = fields.Char(
        string="Prefix",
        help="Enter a prefix value if needed.")
