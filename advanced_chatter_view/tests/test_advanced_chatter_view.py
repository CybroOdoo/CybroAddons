# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
import os

from odoo.modules.module import get_module_path
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestAdvancedChatterView(common.TransactionCase):
    """Test suite for the Advanced Chatter View module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module = cls.env['ir.module.module'].search([
            ('name', '=', 'advanced_chatter_view'),
        ])
        cls.mod_path = get_module_path('advanced_chatter_view')

    def test_01_module_installed(self):
        """Verify that advanced_chatter_view is installed properly."""
        self.assertTrue(
            self.module, "Module advanced_chatter_view must exist."
        )
        self.assertEqual(
            self.module.state,
            'installed',
            "Module advanced_chatter_view should be in 'installed' state.",
        )

    def test_02_manifest_metadata(self):
        """Verify module manifest values conform to requirements."""
        self.assertTrue(self.module.author)
        self.assertTrue(self.module.website)
        self.assertEqual(self.module.license, 'LGPL-3')
        self.assertEqual(self.module.installed_version, '20.0.1.0.0')

    def test_03_static_resources_exist(self):
        """Verify all declared assets and documentation files exist."""
        self.assertTrue(
            self.mod_path,
            "Module path for advanced_chatter_view must exist.",
        )
        required_files = [
            'static/src/lib/bootstrap-icons/bootstrap-icons.css',
            'static/src/lib/bootstrap-icons/fonts/bootstrap-icons.woff2',
            'static/src/css/chatter_topbar.css',
            'static/src/js/chatter_container.js',
            'static/src/xml/chatter.xml',
            'static/description/icon.png',
            'static/description/banner.jpg',
            'static/description/index.html',
            'static/description/assets/screenshots/1.png',
            'static/description/assets/screenshots/2.png',
            'static/description/assets/screenshots/3.png',
            'static/description/assets/screenshots/4.png',
            'static/tests/tours/advanced_chatter_view_tour.js',
            'static/tests/chatter/advanced_chatter_view.test.js',
            'README.rst',
            'doc/RELEASE_NOTES.md',
        ]
        for rel_path in required_files:
            full_path = os.path.join(self.mod_path, rel_path)
            self.assertTrue(
                os.path.isfile(full_path),
                f"Required asset {rel_path} was not found on filesystem at "
                f"{full_path}.",
            )
            self.assertGreater(
                os.path.getsize(full_path),
                0,
                f"Asset {rel_path} must not be empty.",
            )

    def test_04_js_patch_and_xml_definitions(self):
        """Verify JavaScript and XML template structure and syntax."""
        js_path = os.path.join(
            self.mod_path, 'static/src/js/chatter_container.js'
        )
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()

        self.assertIn('@odoo-module', js_content)
        self.assertIn('@mail/chatter/web_portal_project/chatter', js_content)
        self.assertIn('patch(Chatter.prototype', js_content)
        self.assertIn('_onClickSendMessage', js_content)
        self.assertIn('_onClickLogNote', js_content)
        self.assertIn('_onClickActive', js_content)
        self.assertIn('_onClickCross', js_content)

        self.assertNotIn('document.querySelectorAll', js_content)

        xml_path = os.path.join(self.mod_path, 'static/src/xml/chatter.xml')
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        self.assertIn('name="mail.ChatterAdvanced"', xml_content)
        self.assertIn('t-inherit="mail.Chatter"', xml_content)
        self.assertNotIn('t-esc=', xml_content)
        self.assertNotIn('owl="1"', xml_content)
        self.assertNotIn('style=', xml_content)
        self.assertNotIn('position="replace"', xml_content)
        self.assertNotIn('Please wait', xml_content)
        self.assertNotIn('t-ref="this.rootRef"', xml_content)

    def test_05_css_scoped_selectors(self):
        """Verify CSS selectors are properly scoped and avoid form
        pollution.
        """
        css_path = os.path.join(
            self.mod_path, 'static/src/css/chatter_topbar.css'
        )
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        unscoped_patterns = [
            '.icon {',
            '.hide {',
            '.o_form_sheet_bg {',
            '.o_form_editable {',
            '.o_form_statusbar {',
            '.o_form_sheet {',
        ]
        for pattern in unscoped_patterns:
            self.assertNotIn(
                pattern,
                css_content,
                f"Unscoped global selector '{pattern}' must not exist in CSS.",
            )
