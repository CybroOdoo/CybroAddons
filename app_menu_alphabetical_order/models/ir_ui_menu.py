# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev K P(<https://www.cybrosys.com>)
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
from odoo import api, models, tools


class IrUiMenu(models.Model):
    """Extends the 'ir.ui.menu' model to customize menu behavior.
    It provides methods to handle menu sorting and to create ascending menus.
    """
    _inherit = 'ir.ui.menu'
    _order = 'name'

    @api.model
    def menu_ascending(self):
        """Sort top-level menus in ascending order."""
        menus = self.env['ir.ui.menu'].search([('parent_id', '=', False)],
                                              order="name asc")
        menu_sequence = 1
        for menu_item in menus:
            menu_item.sequence = menu_sequence
            menu_sequence += 1

    @api.model
    @tools.ormcache_context('self._uid', 'debug', keys=('lang',))
    def load_menus(self, debug):
        """Override method to sort menus based on their names.
        This method is used to load menus and sort them based on their names.
        It ensures that the menus are displayed in alphabetical order in the
        user interface."""
        menus = super(IrUiMenu, self).load_menus(debug)
        # Sort the menus based on their names
        menus['root']['children'].sort(
            key=lambda menu_id: menus[menu_id]['name'])
        return menus
