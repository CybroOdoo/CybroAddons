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


class SaleOrderLine(models.Model):
    """Extend sale order lines for Click & Collect pickup."""
    _inherit = 'sale.order.line'

    is_click_and_collect = fields.Boolean(
        string='Click & Collect',
        help='Enable this option to allow Click & Collect pickup for this order line.',
    )
    pos_config_id = fields.Many2one(
        'pos.config',
        string='Pickup Store',
        help='Select the POS store where this product will be collected.',
    )
