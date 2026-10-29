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


class PosConfig(models.Model):
    """Inheriting pos_config model to add field control_discount"""
    _inherit = 'pos.config'

    control_discount = fields.Boolean(string='Control Discount',
                                      help="When enabled, the discount "
                                           "option will be disabled in the "
                                           "Point of Sale, and cashiers will "
                                           "not be able to apply a "
                                           "discount on order lines.")
