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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged
from odoo.tools import file_open

from odoo.addons.theme_petzen.models.theme_utils import (
    PETZEN_HEADER_DISABLE,
    PETZEN_HEADER_ENABLE,
    PETZEN_SHOP_VIEWS,
)


@tagged('post_install', '-at_install', 'theme_petzen')
class TestThemeUtils(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.utils = cls.env['theme.utils']
        cls.website = cls.env['website'].create({'name': 'Petzen Test'})
        theme_cls = cls.env.registry['theme.utils']
        website_cls = cls.env.registry['website']
        for patcher in (
            patch.object(theme_cls, 'enable_view'),
            patch.object(theme_cls, 'disable_view'),
            patch.object(website_cls, 'get_current_website',
                         return_value=cls.website),
        ):
            mock = patcher.start()
            cls.addClassCleanup(patcher.stop)
            if patcher.attribute == 'enable_view':
                cls.enable = mock
            elif patcher.attribute == 'disable_view':
                cls.disable = mock

    def setUp(self):
        super().setUp()
        self.enable.reset_mock()
        self.disable.reset_mock()

    def _logo(self):
        with file_open('theme_petzen/static/src/images/logo.png', 'rb') as f:
            return base64.b64encode(f.read())

    def test_shop_views_enabled(self):
        with patch('odoo.api.Environment.ref', return_value=True):
            self.utils._petzen_enable_shop_views()
        called = [c.args[0] for c in self.enable.call_args_list]
        self.assertEqual(called, PETZEN_SHOP_VIEWS)

    def test_header_views_applied(self):
        with patch('odoo.api.Environment.ref', return_value=True):
            self.utils._petzen_setup_header()
        self.assertEqual(
            [c.args[0] for c in self.disable.call_args_list],
            PETZEN_HEADER_DISABLE)
        self.assertEqual(
            [c.args[0] for c in self.enable.call_args_list],
            PETZEN_HEADER_ENABLE)

    def test_logo_set_only_if_default(self):
        self.website.logo = self.website._default_logo()
        self.utils._petzen_setup_header()
        self.assertEqual(self.website.logo, self._logo())

        custom = base64.b64encode(b'custom-logo')
        self.website.logo = custom
        self.utils._petzen_setup_header()
        self.assertEqual(self.website.logo, custom)

    def test_homepage_header_overlay(self):
        home = self.env['website.page'].search([
            ('url', '=', '/'), ('website_id', '=', self.website.id)], limit=1)
        if not home or 'header_overlay' not in home._fields:
            self.skipTest("No homepage with header_overlay")
        home.header_overlay = False
        self.utils._petzen_setup_header()
        self.assertTrue(home.header_overlay)

    def test_post_copy_runs_both_steps(self):
        with patch.object(self.env.registry['theme.utils'],
                          '_petzen_enable_shop_views') as shop, \
                patch.object(self.env.registry['theme.utils'],
                             '_petzen_setup_header') as header:
            self.utils._theme_petzen_post_copy('theme_petzen')
        shop.assert_called_once()
        header.assert_called_once()