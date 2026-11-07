# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
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
from odoo.tests.common import TransactionCase, new_test_user, tagged

from ..models.utils import get_param

REQUESTS_GET = ('odoo.addons.backend_theme_infinito_plus.models'
                '.add_google_fonts.requests.get')
FONT_CSS = "@font-face { font-family: 'Roboto'; src: url(x.woff2); }"


def _fake_response(text=FONT_CSS):
    response = MagicMock()
    response.text = text
    response.raise_for_status.return_value = None
    return response


@tagged('post_install', '-at_install')
class TestGoogleFont(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Font = self.env['infinito.google.font']

    def test_save_google_font(self):
        with patch(REQUESTS_GET, return_value=_fake_response()):
            font_id = self.Font.save_google_fonts(
                ['Roboto', 'https://fonts.google.com/specimen/Roboto'])
        font = self.Font.browse(font_id)
        self.assertEqual(font.name, 'Roboto')
        self.assertEqual(font.font, FONT_CSS)
        # the new font becomes the active one
        self.assertEqual(
            get_param(self.env, 'backend_theme_infinito_plus.font'),
            str(font_id))

    def test_missing_url_is_rebuilt(self):
        with patch(REQUESTS_GET, return_value=_fake_response()):
            font_id = self.Font.save_google_fonts(['Open Sans', 'undefined'])
        self.assertEqual(
            self.Font.browse(font_id).font_url,
            'https://fonts.google.com/specimen/Open+Sans')

    def test_duplicate_font(self):
        with patch(REQUESTS_GET, return_value=_fake_response()):
            self.Font.save_google_fonts(['Roboto', 'https://x'])
            with self.assertRaises(ValidationError):
                self.Font.save_google_fonts(['Roboto', 'https://x'])

    def test_only_admin_can_add_fonts(self):
        user = new_test_user(self.env, login='font_user',
                             groups='base.group_user')
        with patch(REQUESTS_GET, return_value=_fake_response()):
            with self.assertRaises(AccessError):
                self.Font.with_user(user).save_google_fonts(
                    ['Roboto', 'https://x'])

    def test_download_failure(self):
        with patch(REQUESTS_GET, side_effect=requests.ConnectionError('down')):
            with self.assertRaises(UserError):
                self.Font.save_google_fonts(['Roboto', 'https://x'])
        self.assertFalse(self.Font.search([('name', '=', 'Roboto')]))

    def test_active_font_css_without_font(self):
        self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'backend_theme_infinito_plus.font')]).unlink()
        self.assertEqual(self.Font.get_active_font_css(), '')

    def test_active_font_css_with_font(self):
        font = self.Font.create({'name': 'Roboto', 'font': FONT_CSS})
        self.env['ir.config_parameter'].sudo().set_str(
            'backend_theme_infinito_plus.font', str(font.id))
        css = self.Font.get_active_font_css()
        self.assertIn(FONT_CSS, css)
        self.assertIn("font-family: 'Roboto', sans-serif", css)

    def test_active_font_css_strips_unsafe_characters(self):
        font = self.Font.create({'name': "Bad';}</style>", 'font': ''})
        self.env['ir.config_parameter'].sudo().set_str(
            'backend_theme_infinito_plus.font', str(font.id))
        css = self.Font.get_active_font_css()
        self.assertNotIn('</style>', css)
        self.assertNotIn("';}", css)

    def test_active_font_css_deleted_font(self):
        font = self.Font.create({'name': 'Gone', 'font': ''})
        self.env['ir.config_parameter'].sudo().set_str(
            'backend_theme_infinito_plus.font', str(font.id))
        font.unlink()
        self.assertEqual(self.Font.get_active_font_css(), '')

    def test_active_font_css_invalid_value(self):
        self.env['ir.config_parameter'].sudo().set_str(
            'backend_theme_infinito_plus.font', 'abc')
        self.assertEqual(self.Font.get_active_font_css(), '')