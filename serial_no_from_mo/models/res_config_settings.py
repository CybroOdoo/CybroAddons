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


class ResConfigSettings(models.TransientModel):
    """ Res Config Settings model for managing configuration settings.
    This model extends the base `res.config.settings` model to add
    custom fields for configuring serial number selection method,
    number of digits, and prefix. """
    _inherit = 'res.config.settings'

    serial_selection = fields.Selection(
        [('global', 'Global'), ('product_wise', 'Product Wise')],
        string="Choose Method",
        help="Select the method for generating serial numbers: global or"
             " product-wise.",
        config_parameter='serial_no_from_mo.serial_selection')
    mo_serial_digit = fields.Integer(
        string="Number of Digits",
        help="Specify the number of digits to use for the serial numbers.",
        config_parameter='serial_no_from_mo.mo_serial_digit')
    mo_serial_prefix = fields.Char(
        string="Prefix",
        help="Specify the prefix to be added to the serial numbers.",
        config_parameter='serial_no_from_mo.mo_serial_prefix')
    is_serial_selection = fields.Boolean(
        string="Serial Number Selection Method",
        help="Enable or disable the serial number selection method.",
        config_parameter='serial_no_from_mo.is_serial_selection')
