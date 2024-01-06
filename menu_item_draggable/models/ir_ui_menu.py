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
from odoo import api, fields, models, tools
from odoo.osv import expression


class IrUiMenu(models.Model):
    """Inherits ir.ui.menu."""
    _inherit = 'ir.ui.menu'

    user_id = fields.Many2one('res.users')

    @api.model
    @tools.ormcache_context('self._uid', keys=('lang',))
    def load_menus(self, debug):
        """Loads all menu items (all applications and their sub-menus).
        :return: the menu root
        :rtype: dict('children': menu_nodes)
        """
        fields = ['name', 'sequence', 'parent_id', 'action', 'web_icon',
                  'web_icon_data']
        menu_roots = (self.env.user.lst_menu.replace("'", '').
                      replace("[", '').replace("]", '').
                      replace(',', '').split()) \
            if self.env.user.lst_menu else []
        if menu_roots:
            menu_lst = [self.sudo().search(
                [('id', '=', val), ('parent_id', '=', False)])
                for val in menu_roots]
            menu_roots = self.sudo().search([('id', 'not in', menu_roots),
                                             ('parent_id', '=', False)]). \
                concat(*menu_lst)
            sequence_lst = sorted(menu_roots.mapped('sequence'))
            for index, rec in enumerate(menu_roots):
                if index < len(sequence_lst):
                    rec.sequence = sequence_lst[index]
        else:
            menu_roots = self.get_user_roots()
        menu_roots_data = menu_roots.read(fields) if menu_roots else []

        menu_root = {'id': False, 'name': 'root', 'parent_id': [-1, ''],
                     'children': [menu['id'] for menu in menu_roots_data]}
        all_menus = {'root': menu_root}
        if not menu_roots_data:
            return all_menus
        menus_domain = [('id', 'child_of', menu_roots.ids)]
        blacklisted_menu_ids = self._load_menus_blacklist()
        if blacklisted_menu_ids:
            menus_domain = expression.AND(
                [menus_domain, [('id', 'not in', blacklisted_menu_ids)]])
        menus = self.search(menus_domain)
        menu_items = menus.read(fields)
        menu_items.extend(menu_roots_data)
        menu_items_map = {menu_item["id"]: menu_item for menu_item in
                          menu_items}
        for menu_item in menu_items:
            menu_item.setdefault('children', [])
            parent = menu_item['parent_id'] and menu_item['parent_id'][0]
            menu_item['xmlid'] = (menu_roots + menus)._get_menuitems_xmlids()\
                                                     .get(menu_item['id'], "")
            if parent in menu_items_map:
                menu_items_map[parent].setdefault('children', [])\
                                      .append(menu_item['id'])
        all_menus.update(menu_items_map)
        for menu, menu_data in all_menus.items():
            menu_data['children'].sort(key=lambda id: all_menus[id]['sequence'])

        def set_app_id(app_id, menu):
            menu['app_id'] = app_id
            for child_id in menu['children']:
                set_app_id(app_id, all_menus[child_id])

        for app in menu_roots_data:
            app_id = app['id']
            set_app_id(app_id, all_menus[app_id])
        all_menus = {menu['id']: menu for menu in all_menus.values() if
                     menu.get('app_id')}
        all_menus['root'] = menu_root
        return all_menus
