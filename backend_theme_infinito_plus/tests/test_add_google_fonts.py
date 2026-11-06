# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3)   , Version 3.
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
from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user

FAKE_CSS = "@font-face { font-family: 'Roboto'; src: url(x.woff2); }"
REQUESTS_GET = ('odoo.addons.backend_theme_infinito_plus.models.'
                'add_google_fonts.requests.get')
FONT_PARAM = 'backend_theme_infinito_plus.font'


@tagged('post_install', '-at_install')
class TestGoogleFont(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Font = self.env['infinito.google.font']
        patcher = patch(REQUESTS_GET, return_value=MagicMock(text=FAKE_CSS))
        self.mock_get = patcher.start()
        self.addCleanup(patcher.stop)

    def test_save_google_fonts(self):
        font_id = self.Font.save_google_fonts(
            ['Roboto', 'https://fonts.google.com/specimen/Roboto'])
        rec = self.Font.browse(font_id)
        self.assertEqual(rec.name, 'Roboto')
        self.assertIn('font-face', rec.font)
        param = self.env['ir.config_parameter'].sudo().get_param(FONT_PARAM)
        self.assertEqual(param, str(font_id))

    def test_missing_url_is_rebuilt(self):
        for url in ('undefined', ''):
            font_id = self.Font.save_google_fonts(['Open Sans %s' % (url or 'x'), url])
            self.assertIn('fonts.google.com/specimen/Open+Sans',
                          self.Font.browse(font_id).font_url)

    def test_duplicate_font(self):
        self.Font.save_google_fonts(['Roboto', 'https://x'])
        with self.assertRaises(ValidationError):
            self.Font.save_google_fonts(['Roboto', 'https://x'])

    def test_invalid_name(self):
        with self.assertRaises(ValidationError):
            self.Font.save_google_fonts(['Bad;Name{}', ''])
        with self.assertRaises(ValidationError):
            self.Font.create({'name': 'a{b}'})

    def test_only_admin_can_add_font(self):
        user = new_test_user(self.env, login='font_plain_user', groups='base.group_user')
        with self.assertRaises(AccessError):
            self.Font.with_user(user).save_google_fonts(['Roboto', 'https://x'])

    def test_get_css(self):
        self.assertEqual(self.Font.get_css('Open Sans'), FAKE_CSS)
        args, kwargs = self.mock_get.call_args
        self.assertIn('family=Open+Sans', args[0])
        self.assertEqual(kwargs['timeout'], 5)

    def test_get_css_download_error(self):
        self.mock_get.side_effect = requests.RequestException('boom')
        with self.assertRaises(UserError):
            self.Font.get_css('Roboto')

    def test_active_font_css(self):
        params = self.env['ir.config_parameter'].sudo()
        self.assertEqual(self.Font.get_active_font_css(), '')
        self.Font.save_google_fonts(['Roboto', 'https://x'])
        css = self.Font.get_active_font_css()
        self.assertIn('@font-face', css)
        self.assertIn("font-family: 'Roboto'", css)
        for value in ('0', 'abc', '999999'):
            params.set_param(FONT_PARAM, value)
            self.assertEqual(self.Font.get_active_font_css(), '')

    def test_trailing_newline_rejected(self):
        with self.assertRaises(ValidationError):
            self.Font.create({'name': 'Roboto\n'})