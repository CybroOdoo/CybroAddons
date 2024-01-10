# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Megha A P (odoo@cybrosys.com)
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
################################################################################
from odoo import api, models


class MenuItemDraggable(models.Model):
    """Model used to fetch menu item details"""
    _name = 'menu.item.draggable'
    _description = "Data of menu items in each module"

    @api.model
    def get_menu_item(self, menu_id, inner_text):
        """This function is used to get menu item details of clicked menu in
        the screen, according to selected menu fetching parent menu and
        related menu items, then can change sequences according to drag"""
        if menu_id is not None:
            selected_menu = self.env['ir.ui.menu'].browse(menu_id)
            all_menus = self.env['ir.ui.menu'].search([
                ('parent_id', '=', selected_menu.parent_id.id)])
            menu_sequence_list = all_menus.mapped('sequence')
            menu_count = 0
            for text in inner_text:
                each_menu = self.env['ir.ui.menu'].search(
                    [('name', '=', text)])
                if menu_count == 0:
                    each_menu.sequence = menu_sequence_list[menu_count]
                else:
                    if menu_sequence_list[menu_count] == menu_sequence_list[menu_count-1]:
                        each_menu.sequence = menu_sequence_list[menu_count] + 1
                    else:
                        each_menu.sequence = menu_sequence_list[menu_count]
                menu_count += 1
        return True
