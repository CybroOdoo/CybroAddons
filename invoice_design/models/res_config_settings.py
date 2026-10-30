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
    """Adds the custom invoice options to the settings."""
    _inherit = 'res.config.settings'

    is_custom_invoice = fields.Boolean(
        string='Custom Invoice',
        config_parameter='invoice_design.is_custom_invoice',
        help="Enable to print custom invoices")
    invoice_design_id = fields.Many2one(
        'invoice.design',
        config_parameter='invoice_design.invoice_design',
        help="Choose your custom design")
