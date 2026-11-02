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
"""Configuration settings for Cancel MO module."""
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited res.config.settings to add cancel MO parameters."""
    _inherit = 'res.config.settings'

    is_cancel_inventory_moves = fields.Boolean(string="Cancel Inventory Moves",
                                               help="Whether to cancel the "
                                                    "inventory moves",
                                               config_parameter="cancel_mo"
                                                                ".is_cancel_inventory_moves")
    is_cancel_workorder = fields.Boolean(string="Cancel Work Orders",
                                         help="Whether to cancel work orders",
                                         config_parameter="cancel_mo"
                                                          ".is_cancel_workorder")
