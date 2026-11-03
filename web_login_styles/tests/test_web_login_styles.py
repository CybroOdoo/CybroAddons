# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
import base64
from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install', 'web_login_styles')
class TestWebLoginStylesModels(TransactionCase):
    """Test suite for web_login_styles models and configuration settings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_param = cls.env['ir.config_parameter'].sudo()
        cls.dummy_png = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
            "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )

    def test_01_res_config_settings_defaults_and_onchange(self):
        """Test onchange_orientation resets background fields."""
        settings = self.env['res.config.settings'].new({
            'orientation': 'left',
            'background': 'color',
            'color': '#ff0000',
            'url': 'https://example.com/bg.png',
            'image': self.dummy_png,
        })
        self.assertEqual(settings.orientation, 'left')
        self.assertEqual(settings.background, 'color')

        settings.orientation = 'default'
        settings.onchange_orientation()
        self.assertFalse(settings.background)
        self.assertFalse(settings.color)
        self.assertFalse(settings.image)
        self.assertFalse(settings.url)

    def test_02_res_config_settings_save_and_get_values(self):
        """Test setting and getting login style configuration parameters."""
        settings = self.env['res.config.settings'].create({
            'orientation': 'middle',
            'background': 'color',
            'color': '#123456',
            'url': 'https://example.com/image.jpg',
            'image': self.dummy_png,
        })
        settings.set_values()

        self.assertEqual(
            self.config_param.get_str('web_login_styles.orientation'),
            'middle',
        )
        self.assertEqual(
            self.config_param.get_str('web_login_styles.background'),
            'color',
        )
        self.assertEqual(
            self.config_param.get_str('web_login_styles.color'),
            '#123456',
        )
        self.assertEqual(
            self.config_param.get_str('web_login_styles.image'),
            self.dummy_png,
        )

        values = self.env['res.config.settings'].get_values()
        self.assertEqual(values.get('image'), self.dummy_png)

    def test_03_res_config_settings_save_image_bytes(self):
        """Test setting binary image using BinaryBytes and empty image."""
        from odoo.tools.binary import BinaryBytes

        raw_bytes = b'sample-raw-bytes-data'
        settings = self.env['res.config.settings'].create({
            'image': BinaryBytes(raw_bytes),
        })
        settings.set_values()
        expected_b64 = base64.b64encode(raw_bytes).decode('ascii')
        self.assertEqual(
            self.config_param.get_str('web_login_styles.image'),
            expected_b64,
        )

        # Test empty image branch
        settings.image = False
        settings.set_values()
        self.assertEqual(
            self.config_param.get_str('web_login_styles.image'),
            '',
        )

    def test_04_ir_attachment_is_background(self):
        """Test ir.attachment is_background field."""
        attachment = self.env['ir.attachment'].create({
            'name': 'Test Login Background',
            'type': 'binary',
            'is_background': True,
        })
        self.assertTrue(attachment.is_background)
        found = self.env['ir.attachment'].search([
            ('is_background', '=', True),
            ('id', '=', attachment.id),
        ])
        self.assertEqual(found, attachment)


@tagged('post_install', '-at_install', 'web_login_styles')
class TestWebLoginStylesHttp(HttpCase):
    """HTTP integration tests for login styles and routes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_param = cls.env['ir.config_parameter'].sudo()
        cls.dummy_png = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
            "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )

    def test_05_http_login_default(self):
        """Test /web/login with default orientation."""
        self.config_param.set_str('web_login_styles.orientation', 'default')
        res = self.url_open('/web/login')
        self.assertEqual(res.status_code, 200)

    def test_06_http_login_left_color(self):
        """Test /web/login with left orientation and background color."""
        self.config_param.set_str('web_login_styles.orientation', 'left')
        self.config_param.set_str('web_login_styles.background', 'color')
        self.config_param.set_str('web_login_styles.color', '#4a90e2')
        res = self.url_open('/web/login')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'#4a90e2', res.content)

    def test_07_http_login_right_image(self):
        """Test /web/login with right orientation and image background."""
        self.config_param.set_str('web_login_styles.orientation', 'right')
        self.config_param.set_str('web_login_styles.background', 'image')
        self.config_param.set_str('web_login_styles.image', self.dummy_png)
        res = self.url_open('/web/login')
        self.assertEqual(res.status_code, 200)
        attachments = self.env['ir.attachment'].sudo().search([
            ('is_background', '=', True),
        ])
        self.assertTrue(bool(attachments))

    def test_08_http_login_middle_url(self):
        """Test /web/login with middle orientation and URL background."""
        img_url = 'https://example.com/custom_bg.png'
        self.config_param.set_str('web_login_styles.orientation', 'middle')
        self.config_param.set_str('web_login_styles.background', 'url')
        self.config_param.set_str('web_login_styles.url', img_url)
        res = self.url_open('/web/login')
        self.assertEqual(res.status_code, 200)
        attachments = self.env['ir.attachment'].sudo().search([
            ('url', '=', img_url),
        ])
        self.assertTrue(bool(attachments))

    def test_09_http_logout(self):
        """Test /web/session/logout endpoint."""
        res = self.url_open('/web/session/logout')
        self.assertIn(res.status_code, (200, 302, 303))
