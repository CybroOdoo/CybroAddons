# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestThemeData(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ThemeData = cls.env['theme.data']
        cls.green_asset = cls.env.ref(
            'vista_backend_theme.vista_theme_palette_green'
        )
        cls.black_asset = cls.env.ref(
            'vista_backend_theme.vista_theme_palette_black'
        )
        cls.admin_user = cls.env.ref('base.user_admin')
        cls.normal_user = cls.env['res.users'].create({
            'name': 'Theme Test User',
            'login': 'theme_test_user',
            'email': 'theme_test@example.com',
            'group_ids': [
                (6, 0, [cls.env.ref('base.group_user').id])
            ],
        })

    def test_01_default_theme(self):
        """Test default theme when no palette is active."""
        self.green_asset.active = False
        self.black_asset.active = False
        theme = self.ThemeData._get_current_theme()
        self.assertEqual(theme, 'blue')

    def test_02_get_current_theme_green(self):
        """Test green theme detection."""
        self.green_asset.active = True
        self.black_asset.active = False
        self.assertEqual(
            self.ThemeData._get_current_theme(),
            'green'
        )

    def test_03_get_current_theme_black(self):
        """Test black theme detection."""
        self.green_asset.active = False
        self.black_asset.active = True
        self.assertEqual(
            self.ThemeData._get_current_theme(),
            'black'
        )

    def test_04_get_current_theme_priority(self):
        """Test theme detection when multiple palettes are active."""
        self.green_asset.active = True
        self.black_asset.active = True
        # Green is checked first in THEME_ASSETS.
        self.assertEqual(
            self.ThemeData._get_current_theme(),
            'green'
        )

    def test_05_set_green_theme(self):
        """Test administrator can activate green theme."""
        wizard = self.ThemeData.with_user(self.admin_user)
        result = wizard.set_theme('green')
        self.assertTrue(result)
        self.assertTrue(self.green_asset.active)
        self.assertFalse(self.black_asset.active)

    def test_06_set_black_theme(self):
        """Test administrator can activate black theme."""
        wizard = self.ThemeData.with_user(self.admin_user)
        result = wizard.set_theme('black')
        self.assertTrue(result)
        self.assertFalse(self.green_asset.active)
        self.assertTrue(self.black_asset.active)

    def test_07_set_blue_theme(self):
        """Test selecting blue deactivates replacement palettes."""
        wizard = self.ThemeData.with_user(self.admin_user)
        self.green_asset.active = True
        self.black_asset.active = True
        result = wizard.set_theme('blue')
        self.assertTrue(result)
        self.assertFalse(self.green_asset.active)
        self.assertFalse(self.black_asset.active)

    def test_08_invalid_theme(self):
        """Test invalid theme selection."""
        wizard = self.ThemeData.with_user(self.admin_user)
        result = wizard.set_theme('red')
        self.assertFalse(result)

    def test_09_non_admin_access(self):
        """Test normal users cannot change the theme."""
        wizard = self.ThemeData.with_user(self.normal_user)
        with self.assertRaises(AccessError):
            wizard.set_theme('green')

    def test_10_action_apply(self):
        """Test action_apply returns client reload action."""
        wizard = self.ThemeData.create({
            'name': 'green',
        })
        with patch.object(
            type(wizard),
            'set_theme',
            return_value=True
        ) as mocked_set_theme:
            result = wizard.action_apply()
            mocked_set_theme.assert_called_once_with('green')
        self.assertEqual(result, {
            'type': 'ir.actions.client',
            'tag': 'reload',
        })

    def test_11_apply_menu_icons(self):
        """Test root menu icons are updated correctly."""
        wizard = self.ThemeData.with_user(self.admin_user)
        menu = self.env.ref('base.menu_administration')
        self.assertTrue(menu)
        wizard._apply_menu_icons('green')
        menu.invalidate_recordset(['web_icon_data'])
        self.assertTrue(
            menu.web_icon_data,
            'Menu icon should be updated.'
        )

    def test_12_missing_menu_icon(self):
        """Test missing icon does not interrupt menu processing."""
        wizard = self.ThemeData.with_user(self.admin_user)
        with patch.object(
            type(self.env['ir.ui.menu']),
            '_read_image',
            return_value=False
        ):
            wizard._apply_menu_icons('green')
        # The method should complete without raising an exception.
        self.assertTrue(True)

    def test_13_restore_menu_icons(self):
        """Test original root menu icons are restored."""
        import base64
        wizard = self.ThemeData.with_user(self.admin_user)
        menu = self.env['ir.ui.menu'].sudo().search([
            ('parent_id', '=', False),
            ('web_icon', '!=', False),
        ], limit=1)
        if not menu:
            self.skipTest('No root menu with web_icon found.')
        expected_icon = menu._compute_web_icon_data(menu.web_icon)
        wizard._apply_menu_icons('green')
        wizard._restore_menu_icons()
        menu.invalidate_recordset(['web_icon_data'])
        actual_icon = menu.web_icon_data
        expected_data = base64.b64decode(expected_icon)
        actual_data = base64.b64decode(actual_icon)
        self.assertEqual(
            actual_data,
            expected_data,
            'Original menu icon should be restored.'
        )