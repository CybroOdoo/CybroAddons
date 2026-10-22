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


class ResUsers(models.Model):
    """Add POS config and buttons in the user form view"""
    _inherit = 'res.users'

    pos_config_ids = fields.Many2many('pos.config',
                                       string="Point of Sale",
                                       help="POS configurations where button restrictions apply. If empty, restrictions apply to all.")

    pos_button_ids = fields.Many2many('pos.button',
                                       string="POS Buttons",
                                       help="POS buttons that should be restricted for the user.")

    def pos_button_visibility(self, hide_buttons):
        """This is used to return the restricted button name"""
        pos_buttons = self.env['pos.button'].browse(hide_buttons).mapped('name')
        return pos_buttons

    @api.model
    def _load_pos_data_fields(self, config):
        """
        Load POS fields for the user.

        pos_config_ids → POS configurations where the user should have restrictions
        pos_button_ids → buttons that should be hidden for the user
        """

        result = super()._load_pos_data_fields(config)
        result += ['pos_button_ids', 'pos_config_ids']
        return result

