# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.

#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inheriting res_config_settings model to add field control_discount"""
    _inherit = 'res.config.settings'

    control_discount = fields.Boolean(string='Control Discount',
                                      related="pos_config_id.control_discount",
                                      readonly=False,
                                      help="Enable to control the discount")
