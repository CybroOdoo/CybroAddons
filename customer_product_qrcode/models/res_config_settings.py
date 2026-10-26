# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Extends the res.config.settings model to include configuration
    settings for QR code prefixes."""
    _inherit = 'res.config.settings'

    customer_prefix = fields.Char(
        string="Customer QR Prefix",
        config_parameter='customer_product_qr.config.customer_prefix',
        help='Customer QR prefix'
    )
    product_prefix = fields.Char(
        string="Product QR Prefix",
        config_parameter='customer_product_qr.config.product_prefix',
        help='Product QR prefix'
    )
