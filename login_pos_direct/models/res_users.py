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
    """Inherit `res.users` to support assigning a direct login POS configuration."""

    _inherit = "res.users"

    pos_conf_id = fields.Many2one(
        comodel_name='pos.config',
        string="POS Configuration",
        check_company=True,
        domain="[('company_id', 'in', [company_id, False])]",
        help="Select POS configuration to directly login for this user.",
    )

    @api.onchange('pos_conf_id')
    def _onchange_pos_conf_id(self):
        """Warn user if attempting to assign POS config without POS User group."""
        if self.pos_conf_id and not self.has_group('point_of_sale.group_pos_user'):
            return {
                'warning': {
                    'title': self.env._("Access Denied"),
                    'message': self.env._(
                        "This user must be in the POS User group to set a POS "
                        "configuration.",
                    ),
                },
            }
        return None

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure pos_conf_id is cleared if user lacks POS group on creation."""
        users = super().create(vals_list)
        for user in users:
            if user.pos_conf_id and not user.has_group('point_of_sale.group_pos_user'):
                user.sudo().pos_conf_id = False
        return users

    def write(self, vals):
        """Ensure pos_conf_id is cleared if user lacks POS group on write."""
        res = super().write(vals)
        for user in self:
            if user.pos_conf_id and not user.has_group('point_of_sale.group_pos_user'):
                user.sudo().pos_conf_id = False
        return res
