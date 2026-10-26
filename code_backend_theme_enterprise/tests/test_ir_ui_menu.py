# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aswin A K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, tagged

from ..models.ir_ui_menu import ICON_PATH, MENU_ICONS


@tagged('post_install', '-at_install')
class TestIrUiMenu(TransactionCase):
    """Tests for the theme icons applied to the root menus."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Menu = cls.env['ir.ui.menu']

    def test_known_root_menu_gets_theme_icon(self):
        """A root menu with a known name receives the matching theme icon."""
        menu = self.Menu.create({'name': 'Sales'})
        self.Menu._cbt_apply_theme_icons()
        self.assertEqual(menu.web_icon, ICON_PATH + MENU_ICONS['Sales'])

    def test_existing_icon_is_replaced(self):
        """An icon set by another module is replaced by the theme icon."""
        menu = self.Menu.create({
            'name': 'Contacts',
            'web_icon': 'base,static/description/icon.png',
        })
        self.Menu._cbt_apply_theme_icons()
        self.assertEqual(menu.web_icon, ICON_PATH + MENU_ICONS['Contacts'])

    def test_archived_root_menu_gets_theme_icon(self):
        """Archived root menus are updated too, for when they are restored."""
        menu = self.Menu.create({'name': 'Project', 'active': False})
        self.Menu._cbt_apply_theme_icons()
        self.assertEqual(menu.web_icon, ICON_PATH + MENU_ICONS['Project'])

    def test_unknown_root_menu_is_untouched(self):
        """A root menu without a theme icon keeps its own icon."""
        menu = self.Menu.create({
            'name': 'CBT Unknown App',
            'web_icon': 'base,static/description/icon.png',
        })
        self.Menu._cbt_apply_theme_icons()
        self.assertEqual(menu.web_icon, 'base,static/description/icon.png')

    def test_child_menu_is_untouched(self):
        """Only root menus are themed, sub-menus keep their icon."""
        parent = self.Menu.create({'name': 'CBT Parent App'})
        child = self.Menu.create({'name': 'Sales', 'parent_id': parent.id})
        self.Menu._cbt_apply_theme_icons()
        self.assertFalse(child.web_icon)

    def test_settings_and_apps_menus_use_theme_icons(self):
        """The Settings and Apps menus use the theme icons."""
        self.assertEqual(self.env.ref('base.menu_administration').web_icon,
                         ICON_PATH + 'settings.png')
        self.assertEqual(self.env.ref('base.menu_management').web_icon,
                         ICON_PATH + 'apps.png')
