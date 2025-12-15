# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, models


class IrUiMenu(models.Model):
    """Extend ir.ui.menu to apply role-based UI restrictions."""
    _inherit = 'ir.ui.menu'

    @api.model
    def _visible_menu_ids(self, debug=False):
        """Override to dynamically hide menus based on role management."""
        visible_menu_ids = super()._visible_menu_ids(debug=debug)
        role = self.env.user.access_role_id
        hidden_menu_ids = set()
        if role.role_management_id and role.role_management_id.menu_ids:
            hidden_menu_ids.update(role.role_management_id.menu_ids.ids)
        return visible_menu_ids - hidden_menu_ids

    @api.model
    def load_menus(self, debug=False):
        """Override to ensure menus are always fresh when loaded."""
        return super().load_menus(debug=debug)
