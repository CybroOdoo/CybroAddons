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
import json

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Vendor approval settings of the tender management."""
    _inherit = 'res.config.settings'

    auto_approval = fields.Boolean(
        config_parameter='advanced_tender_management.auto_approval',
        help="Automatically approves vendor and grants portal access",
    )
    manual_approval_users_ids = fields.Many2many(
        'res.users',
        string="Approval Users",
        help="Users who can grant portal access to vendors"
    )

    @api.model
    def get_values(self):
        """Read the manual approval users from the system parameters."""
        res = super().get_values()
        users_param = self.env['ir.config_parameter'].sudo().get_str(
            'advanced_tender_management.manual_approval_users_ids')
        user_ids = json.loads(users_param) if users_param else []
        res['manual_approval_users_ids'] = self.env['res.users'].browse(user_ids).exists()
        return res

    def set_values(self):
        """Store the manual approval users in the system parameters."""
        res = super().set_values()
        self.env['ir.config_parameter'].sudo().set_str(
            'advanced_tender_management.manual_approval_users_ids',
            json.dumps(self.manual_approval_users_ids.ids))
        return res
