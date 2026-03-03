# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu K P (odoo@cybrosys.com)
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
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):
    """Extends the 'stock.warehouse' model to add functionality for restricting
     stock location access to specific users within the system."""
    _inherit = "stock.warehouse"

    user_ids = fields.Many2many(
        comodel_name='res.users', string='Allowed Users',
        domain=lambda self: [
            ('groups_id', 'in', self.env.ref('stock.group_stock_user').id)],
        help='Allowed users to this Warehouse.')
    restrict_location = fields.Boolean(
        string='Restrict Stock Location for this Warehouse',
        help='Restrict stock location of this warehouse to the selected '
             'users.')

    @api.onchange('user_ids')
    def _onchange_user_ids(self):
        """Ensure current user is always included when restriction is enabled"""
        if self.restrict_location and self.env.user not in self.user_ids:
            self.user_ids = [(4, self.env.user.id)]

    def write(self, vals):
        """Override the write method to prevent the current user from being
        removed from the user_ids Many2many field and update user settings."""

        if 'user_ids' in vals:
            current_user = self.env.user
            for warehouse in self:
                if warehouse.restrict_location:
                    new_user_ids = self._compute_new_user_ids(warehouse.user_ids, vals['user_ids'])
                    if current_user.id not in new_user_ids:
                        raise ValidationError(
                            "You cannot remove yourself from the allowed users "
                            "of this warehouse."
                        )

        res = super(StockWarehouse, self).write(vals)

        if 'user_ids' in vals or 'restrict_location' in vals:
            self._update_user_restrictions()

        return res

    def _compute_new_user_ids(self, current_user_ids, user_ids_commands):
        """Compute the final user IDs after applying Many2many commands"""
        user_ids = set(current_user_ids.ids)

        for command in user_ids_commands:
            if command[0] == 4:  # Add
                user_ids.add(command[1])
            elif command[0] == 3:  # Remove
                user_ids.discard(command[1])
            elif command[0] == 6:  # Replace
                user_ids = set(command[2])
            elif command[0] == 5:  # Clear
                user_ids = set()

        return list(user_ids)

    def _update_user_restrictions(self):
        """Update user restriction settings based on warehouse configuration"""
        for warehouse in self:
            if not warehouse.company_id:
                continue

            valid_users = warehouse.user_ids.filtered(
                lambda u: warehouse.company_id in u.company_ids
            )

            if warehouse.restrict_location and valid_users:
                valid_users.sudo().with_context(
                    allowed_company_ids=warehouse.company_id.ids
                ).write({
                    'restrict_location': True,
                    'allowed_warehouse_ids': [(4, warehouse.id)],
                })
            elif not warehouse.restrict_location and valid_users:
                # Remove this warehouse from users' allowed warehouses
                valid_users.sudo().with_context(
                    allowed_company_ids=valid_users.mapped('company_ids').ids
                ).write({
                    'allowed_warehouse_ids': [(3, warehouse.id)],
                })

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set up user restrictions"""
        warehouses = super(StockWarehouse, self).create(vals_list)
        warehouses._update_user_restrictions()
        return warehouses

    def action_open_users_view(self):
        """Return user basic form view to give restricted location for users"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Users',
            'view_mode': 'tree,form',
            'res_model': 'res.users',
            'domain': [('id', 'in', self.user_ids.ids),
                       ('groups_id', 'not in',
                        [self.env.ref('base.group_system').id])]}