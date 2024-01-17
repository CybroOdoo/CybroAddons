# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
from odoo import api, fields, models


class ResUsers(models.Model):
    """Inherit the class res_users to add field"""
    _inherit = "res.users"

    pos_conf_id = fields.Many2one('pos.config', string="POS Configuration",
                                  help='select POS for the user')
    pos_config_ids = fields.Many2many('pos.config', string='Allowed Pos',
                                   help='Allowed Pos for this user')
    show_users = fields.Boolean(string="Show users of pos", default=True,
                                help='Show users in dashboard ( for pos '
                                     'administrators only)')

    @api.model
    def create(self, vals):
        """This method creates a new record for the ResUsers model with the
         provided values. It clears the caches before creating the record."""
        self.clear_caches()
        return super(ResUsers, self).create(vals)

    def write(self, vals):
        """For clearing out existing values and update with new values"""
        self.clear_caches()
        return super(ResUsers, self).write(vals)
