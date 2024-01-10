# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Swetha Anand (odoo@cybrosys.com)
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
##############################################################################
from odoo import api, models


class DraggableHomeMenuItem(models.Model):
    """ Draggable Home Menu """
    _name = 'draggable.home.menu.item'
    _description = 'Draggable Home Menu Item'

    @api.model
    def get_home_menu_item(self, menu_id, menu_items, items):
        menu_list = []
        user = self.env.user
        if user.lst_menu:
            user.lst_menu.replace(user.lst_menu, '')
        user.lst_menu = items
        before_menu = self.env['ir.ui.menu'].sudo().search([
            ('parent_id', '=', None), ('name', '=', menu_items)]).ids
        if menu_id is not None:
            menu = self.env['ir.ui.menu'].sudo().search([('id', '=', menu_id)])
            menu_parent = self.env['ir.ui.menu'].sudo().search([
                ('parent_id', '=', menu.parent_id.id)])
            sequence_list = menu_parent.sudo().mapped('sequence')
            for i, item in enumerate(menu_items):
                menu_item = self.env['ir.ui.menu'].sudo().search([
                    ('name', '=', item)], limit=1)
                menu_item.sequence = sequence_list[i]
                menu_list.append(menu_item.id)
        user.menu_ids = self.env['ir.ui.menu'].search([
            ('parent_id', '=', None), ('id', 'in', menu_list)]).ids
        after_menu = user.menu_ids.ids
        return {
            'type': str(before_menu != after_menu)
        }
