# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby (<https://www.cybrosys.com>)
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
from odoo.tests import common
import odoo.tests


class TestResConfigSettings(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestResConfigSettings, cls).setUpClass()
        cls.settings = cls.env['res.config.settings'].create({
            'orientation': 'left',
            'background': 'color',
            'color': '#ffffff',
            'url': 'http://example.com/image.png',
        })

    def test_onchange_orientation(self):
        """Test that background fields are reset when orientation is 'default'."""
        self.settings.orientation = 'default'
        self.settings.onchange_orientation()
        self.assertFalse(self.settings.background)
        self.assertFalse(self.settings.color)
        self.assertFalse(self.settings.image)
        self.assertFalse(self.settings.url)

    def test_get_set_values(self):
        """Test getting and setting image values in config."""
        test_image = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
        settings = self.env['res.config.settings'].create({
            'image': test_image
        })
        settings.set_values()
        
        values = settings.get_values()
        self.assertEqual(values.get('image'), test_image)


@odoo.tests.common.tagged('post_install', '-at_install')
class TestWebLoginStyles(odoo.tests.HttpCase):

    def setUp(self):
        super().setUp()
        self.param_obj = self.env['ir.config_parameter'].sudo()

    def test_login_orientation_left(self):
        """Test left orientation layout renders correctly."""
        self.param_obj.set_param('web_login_styles.orientation', 'left')
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'float:left;', response.content)

    def test_login_orientation_right(self):
        """Test right orientation layout renders correctly."""
        self.param_obj.set_param('web_login_styles.orientation', 'right')
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'float:right;', response.content)

    def test_login_orientation_middle(self):
        """Test middle orientation layout renders correctly."""
        self.param_obj.set_param('web_login_styles.orientation', 'middle')
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)

    def test_login_orientation_default(self):
        """Test default orientation layout renders correctly."""
        self.param_obj.set_param('web_login_styles.orientation', 'default')
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)

    def test_background_color(self):
        """Test background color is applied correctly."""
        self.param_obj.set_param('web_login_styles.orientation', 'left')
        self.param_obj.set_param('web_login_styles.background', 'color')
        self.param_obj.set_param('web_login_styles.color', '#123456')
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'background-color: #123456', response.content)

    def test_background_url(self):
        """Test background url logic runs without errors."""
        self.param_obj.set_param('web_login_styles.orientation', 'left')
        self.param_obj.set_param('web_login_styles.background', 'url')
        self.param_obj.set_param('web_login_styles.url', 'http://example.com/bg.png')
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)

    def test_background_image(self):
        """Test background image logic runs without errors."""
        test_image = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
        self.param_obj.set_param('web_login_styles.orientation', 'left')
        self.param_obj.set_param('web_login_styles.background', 'image')
        self.param_obj.set_param('web_login_styles.image', test_image)
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
