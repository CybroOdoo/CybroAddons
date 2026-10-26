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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit the base settings to add POS all orders configuration."""
    _inherit = 'res.config.settings'

    pos_all_order = fields.Selection(
        [
            ('current_session', 'Load Orders from the current session'),
            ('past_order', 'Load All past Orders'),
            ('last_n', 'Load all orders of last n days'),
        ],
        string='POS All Orders',
        help='Select order types to load in POS',
        config_parameter='pos_all_orders.pos_all_order',
    )

    n_days = fields.Integer(
        string='Number of Days',
        help='Specify the number of past days to load orders for',
        config_parameter='pos_all_orders.n_days',
    )

    @api.model
    def get_values(self):
        """Get values from the fields."""
        res = super().get_values()
        icp = self.env['ir.config_parameter'].sudo()
        pos_all_order = icp.get_str('pos_all_orders.pos_all_order') or False
        n_days = icp.get_int('pos_all_orders.n_days') or 0
        res.update(
            pos_all_order=pos_all_order,
            n_days=n_days,
        )
        return res

    def set_values(self):
        """Set values in the fields."""
        res = super().set_values()
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_str('pos_all_orders.pos_all_order', self.pos_all_order or False)
        icp.set_int('pos_all_orders.n_days', self.n_days or 0)
        return res
