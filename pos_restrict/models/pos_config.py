# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Busthana Shirin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class PosConfig(models.Model):
    """Class added to Restrict the user for accessing pos"""
    _inherit = 'pos.config'

    users_allowed = fields.Many2many('res.users',
                                     string='Users Allowed',
                                     help='Which shows the specified pos for '
                                          'particular user',
                                     compute='_compute_users_allowed')

    def _compute_users_allowed(self):
        # computes the allowed users in pos
        for this in self:
            # checks is show_users is ticked in user settings
            if this.env.user.show_users:
                this.users_allowed = self.env['res.users'].search(
                    [('allowed_pos', '=', this.id)])
            else:
                this.users_allowed = None
