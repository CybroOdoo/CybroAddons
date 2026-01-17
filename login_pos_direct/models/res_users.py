# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Prathyunnan R (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models, _


class ResUsers(models.Model):
    """
    Inherit `res.users` to add support for assigning a POS configuration
    to users. The feature is restricted to users belonging to the
    `point_of_sale.group_pos_user` group.

    Features:
        - Add a Many2one field `pos_conf_id` to link a user with a POS config.
        - Prevent assignment of POS config if the user is not a POS user.
        - Auto-clear the field when the group is removed.
    """
    _inherit = "res.users"

    pos_conf_id = fields.Many2one(comodel_name='pos.config',
                                  string="POS Configuration",
                                  help='select POS for the user')

    @api.onchange('pos_conf_id')
    def _onchange_pos_conf_id(self):
        """
        Onchange handler for the `pos_conf_id` field.

        Warns the user if they attempt to assign a POS configuration
        while not belonging to the `point_of_sale.group_pos_user` group.

        Returns:
            dict: A warning message for the form view, if access is denied.
        """
        if self.pos_conf_id and not self.has_group(
                'point_of_sale.group_pos_user'):
            return {
                'warning': {
                    'title': _("Access Denied"),
                    'message': _(
                        "This user must be in the POS User group to set a POS "
                        "configuration."),
                }
            }

    def write(self, vals):
        """
        Override the base `write` method to enforce POS group rules.

        After updating a user record:
        - If the user is not in the `point_of_sale.group_pos_user` group
          but has a `pos_conf_id` set, the field is cleared.

        Args:
            vals (dict): The incoming values to be written.

        Returns:
            bool: Result of the parent `write` call.
        """
        res = super().write(vals)
        for user in self:
            if not user.has_group(
                    'point_of_sale.group_pos_user') and user.pos_conf_id:
                user.pos_conf_id = False
        return res
