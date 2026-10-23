# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the GNU LESSER GENERAL PUBLIC LICENSE
#    Version 3 (LGPL-3)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
import base64
import os

from odoo.modules.module import get_module_path
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestWidgetPreviewImage(common.TransactionCase):
    """Test suite for Image Preview Widget module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module = cls.env['ir.module.module'].search([
            ('name', '=', 'widget_preview_image'),
        ])
        # 1x1 transparent GIF bytes in base64
        cls.sample_image_base64 = base64.b64encode(
            b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        ).decode('ascii')

    def test_01_module_installation(self):
        """Verify that widget_preview_image is properly installed."""
        self.assertTrue(self.module, "Module widget_preview_image should exist.")
        self.assertEqual(
            self.module.state,
            'installed',
            "Module widget_preview_image should be in 'installed' state.",
        )

    def test_02_static_resources_exist(self):
        """Verify all declared frontend assets and description files exist."""
        mod_path = get_module_path('widget_preview_image')
        self.assertTrue(mod_path, "Module path for widget_preview_image must exist.")
        required_files = [
            'static/src/js/image_preview_widget.js',
            'static/description/icon.png',
            'static/description/banner.jpg',
            'static/description/index.html',
            'static/description/assets/screenshots/1.png',
            'static/description/assets/screenshots/2.png',
            'static/description/assets/screenshots/3.png',
            'static/description/assets/modules/core.jpg',
            'static/description/assets/modules/accounting.gif',
            'static/description/assets/modules/reminder.jpg',
        ]
        for rel_path in required_files:
            full_path = os.path.join(mod_path, rel_path)
            self.assertTrue(
                os.path.isfile(full_path),
                f"Required asset {rel_path} was not found on filesystem at {full_path}.",
            )
            self.assertGreater(
                os.path.getsize(full_path),
                0,
                f"Asset {rel_path} must not be empty.",
            )

    def test_03_js_asset_syntax_and_registration(self):
        """Verify JavaScript content is valid and contains ImageField patch."""
        mod_path = get_module_path('widget_preview_image')
        js_path = os.path.join(mod_path, 'static/src/js/image_preview_widget.js')
        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("@odoo-module", content)
        self.assertIn("patch(ImageField.prototype", content)
        self.assertIn("enlarged-image", content)
        self.assertIn("image_1920", content)

    def test_04_image_field_model_compatibility(self):
        """Verify records with image fields support full-res and thumbnail access."""
        partner = self.env['res.partner'].create({
            'name': 'Test Image Preview Partner',
            'image_1920': self.sample_image_base64,
        })
        self.assertTrue(partner.image_1920)
        self.assertTrue(hasattr(partner, 'avatar_128'))
