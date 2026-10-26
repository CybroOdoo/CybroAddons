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
    """Add bag charge settings to the configuration settings."""
    _inherit = "res.config.settings"

    is_pos_bag_charges = fields.Boolean(
        related="pos_config_id.is_bag_charges",
        readonly=False,
        string="Enable Bag Charges",
        help="Enable this to show the 'Add Bag' button in the POS."
    )

    pos_bag_category_id = fields.Many2one(
        'pos.category',
        related="pos_config_id.bag_category_id",
        readonly=False,
        string="Bag Category",
        help="Products in this POS category are listed as selectable bags."
    )
