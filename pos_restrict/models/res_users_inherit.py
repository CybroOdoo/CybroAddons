# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_pos = fields.Many2many('pos.config', string='Allowed Pos',
                                   help='Allowed Pos for this user')
    show_users = fields.Boolean(string="Show users of pos", default=True, help='Show users in dashboard ( for pos administrators only)')

    @api.model
    def create(self, vals):
        self.clear_caches()
        return super(ResUsers, self).create(vals)

    def write(self, vals):
        # for clearing out existing values and update with new values
        self.clear_caches()
        return super(ResUsers, self).write(vals)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    users_allowed = fields.Many2many('res.users', compute='get_allowed_users')

    def get_allowed_users(self):
        # computes the allowed users in pos
        for this in self:
            # checks is show_users is ticked in user settings
            if this.env.user.show_users:
                this.users_allowed = self.env['res.users'].search([('allowed_pos', '=', this.id)])
            else:
                this.users_allowed = None
