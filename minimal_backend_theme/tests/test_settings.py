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
import odoo.http
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestThemeSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Start from the defaults whatever the database holds (rolled back).
        cls.env['ir.config_parameter'].sudo().search(
            [('key', '=like', 'minimal_backend_theme.%')],
        ).unlink()
        cls.Settings = cls.env['res.config.settings']
        cls.regular_user = new_test_user(cls.env, login='theme_settings_user', groups='base.group_user')

    def _save(self, **values):
        self.Settings.create(values).execute()

    def test_defaults(self):
        self.assertEqual(self.Settings._minimal_theme_get_settings(), {
            'menu_layout': 'horizontal',
            'dark_mode': False,
            'compact': False,
            'full_width': False,
            'can_edit': True,
        })
        self.assertFalse(
            self.Settings.with_user(self.regular_user)._minimal_theme_get_settings()['can_edit'])

    def test_saved_settings_are_read_back(self):
        self._save(
            minimal_theme_menu_layout='vertical',
            minimal_theme_dark_mode=True,
            minimal_theme_compact=True,
            minimal_theme_full_width=True,
        )
        settings = self.Settings._minimal_theme_get_settings()
        self.assertEqual(
            {key: settings[key] for key in ('menu_layout', 'dark_mode', 'compact', 'full_width')},
            {'menu_layout': 'vertical', 'dark_mode': True, 'compact': True, 'full_width': True},
        )

    def test_quick_settings_and_settings_page_share_values(self):
        """What Quick settings saves is what the Settings page shows."""
        self.Settings.minimal_theme_set_option('menu_layout', 'vertical')
        self.Settings.minimal_theme_set_option('compact', True)
        self.Settings.minimal_theme_set_option('full_width', True)
        self.Settings.minimal_theme_set_option('dark_mode', True)
        form = self.Settings.create({})
        self.assertEqual(form.minimal_theme_menu_layout, 'vertical')
        self.assertTrue(form.minimal_theme_compact)
        self.assertTrue(form.minimal_theme_full_width)
        self.assertTrue(form.minimal_theme_dark_mode)

        # And the other way round: saving the Settings page.
        form.minimal_theme_compact = False
        form.execute()
        self.assertFalse(self.Settings._minimal_theme_get_settings()['compact'])

    def test_only_administrators_change_options(self):
        with self.assertRaises(AccessError):
            self.Settings.with_user(self.regular_user).minimal_theme_set_option('compact', True)
        self.assertFalse(self.Settings._minimal_theme_get_settings()['compact'])

    def test_option_values_are_validated(self):
        with self.assertRaises(ValidationError):
            self.Settings.minimal_theme_set_option('menu_layout', 'diagonal')
        with self.assertRaises(ValidationError):
            self.Settings.minimal_theme_set_option('compact', 'yes')
        with self.assertRaises(ValidationError):
            self.Settings.minimal_theme_set_option('base.secret', True)

    def _color_scheme(self, cookie=None):
        request = type('Request', (), {})()
        request.httprequest = type('HttpRequest', (), {'cookies': {'color_scheme': cookie} if cookie else {}})()
        token = odoo.http.request_var.set(request)
        try:
            return self.env['ir.http'].color_scheme()
        finally:
            odoo.http.request_var.reset(token)

    def test_color_scheme_follows_the_shared_option(self):
        self.assertEqual(self._color_scheme(), 'light')
        self.assertEqual(self._color_scheme('dark'), 'light', "the color_scheme cookie (set by the web client for core widgets) does not decide it")
        self.Settings.minimal_theme_set_option('dark_mode', True)
        self.assertEqual(self._color_scheme(), 'dark')
        self.assertEqual(self._color_scheme('light'), 'dark')

    def test_settings_view_has_section(self):
        arch = self.Settings.get_views([(False, 'form')])['views']['form']['arch']
        self.assertIn('minimal_theme_menu_layout', arch)
        self.assertIn('minimal_theme_search_model_ids', arch)
