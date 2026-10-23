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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherits model 'res.config.settings' to add new fields"""
    _inherit = 'res.config.settings'

    double_validation = fields.Boolean(
        string='Double Validation',
        config_parameter='double_validation_invoice.double_validation',
        help='Enable or disable double validation for invoices. If '
             'enabled, invoices will go through two validation stages.',
    )
    first_valid_limit = fields.Float(
        string='First Validation Limit',
        config_parameter='double_validation_invoice.first_valid_limit',
        help='The monetary limit for the first validation stage. Invoices '
             'with amounts exceeding this limit will require the first '
             'validation.',
    )
    second_valid_limit = fields.Float(
        string='Second Validation Limit',
        config_parameter='double_validation_invoice.second_valid_limit',
        help='The monetary limit for the second validation stage. Invoices '
             'with amounts exceeding this limit will require the second '
             'validation.',
    )
