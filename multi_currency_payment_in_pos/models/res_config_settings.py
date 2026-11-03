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
    """Inherit res.config.settings to provide multi-currency settings for POS."""
    _inherit = 'res.config.settings'

    currency_ids = fields.Many2many(
        related='pos_config_id.currency_ids',
        readonly=False,
    )
    enable_currency = fields.Boolean(
        related='pos_config_id.enable_multicurrency',
        readonly=False,
    )
