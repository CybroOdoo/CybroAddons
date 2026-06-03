# -*- coding: utf-8 -*-
###############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import json
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ Inherited to add more fields and functions. """
    _inherit = 'res.config.settings'

    auto_approval = fields.Boolean(
        string='Auto Approval',
        config_parameter='advanced_tender_management.auto_approval',
        help="Automatically approves vendor and grants portal access",
        default=True
    )
    manual_approval_users_ids = fields.Many2many(
        'res.users',
        string="Approval Users",
        help="Users who can grant portal access to vendors"
    )

    @api.model
    def get_values(self):
        """Override to get manual approval users"""
        res = super(ResConfigSettings, self).get_values()
        manual_approval_users_ids_string = self.env['ir.config_parameter'].sudo().get_param(
            'advanced_tender_management.manual_approval_users_ids'
        )
        manual_approval_users_ids = json.loads(
            manual_approval_users_ids_string) if manual_approval_users_ids_string else []
        manual_approval_users = self.env['res.users'].browse(manual_approval_users_ids)
        res.update({
            'manual_approval_users_ids': manual_approval_users,
        })
        return res

    def set_values(self):
        """Override to save manual approval users"""
        super(ResConfigSettings, self).set_values()
        if self.manual_approval_users_ids:
            manual_approval_users_ids_string = json.dumps(self.manual_approval_users_ids.ids)
            self.env['ir.config_parameter'].sudo().set_param(
                'advanced_tender_management.manual_approval_users_ids', manual_approval_users_ids_string
            )
        else:
            self.env['ir.config_parameter'].sudo().set_param(
                'advanced_tender_management.manual_approval_users_ids', '[]'
            )
