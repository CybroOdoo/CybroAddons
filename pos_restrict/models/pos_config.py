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


class PosConfig(models.Model):
    """Class added to restrict user access to Point of Sale."""
    _inherit = 'pos.config'

    users_allowed_ids = fields.Many2many(
        comodel_name='res.users',
        string='Users Allowed',
        help='Shows the users allowed to access this Point of Sale configuration.',
        compute='_compute_users_allowed_ids',
    )

    @api.depends_context('uid')
    def _compute_users_allowed_ids(self):
        if not self.env.user.show_users:
            self.users_allowed_ids = False
            return
        users = self.env['res.users'].sudo().search([('allowed_pos_ids', 'in', self.ids)])
        for config in self:
            config.users_allowed_ids = users.filtered(
                lambda user: config.id in user.allowed_pos_ids.ids
            )
