# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R(odoo@cybrosys.com)
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
###############################################################################
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
