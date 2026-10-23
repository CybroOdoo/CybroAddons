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
    """Add the auto post and auto send invoice options to the settings
    page: `is_create_invoice_delivery_validate` and `is_auto_send_invoice`.
    """
    _inherit = "res.config.settings"

    is_create_invoice_delivery_validate = fields.Boolean(
        string="Auto Post Invoice",
        config_parameter=(
            'automatic_invoice_and_post.is_create_invoice_delivery_validate'),
        help="Create and post the invoice on delivery validation")

    is_auto_send_invoice = fields.Boolean(
        string="Auto Send Invoice",
        config_parameter='automatic_invoice_and_post.is_auto_send_invoice',
        help="Send the invoice to the customer by email on delivery "
             "validation")
