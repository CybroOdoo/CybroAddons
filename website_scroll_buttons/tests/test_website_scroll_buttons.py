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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.modules.module import get_manifest
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWebsiteScrollButtons(TransactionCase):
    """Unit test suite for Website Scroll Buttons module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env.ref(
            'website_scroll_buttons.website_scroll_buttons',
            raise_if_not_found=False,
        )

    def test_scroll_buttons_template_exists(self):
        """Verify that the website scroll buttons template exists in the environment."""
        self.assertIsNotNone(
            self.template,
            "Template website_scroll_buttons.website_scroll_buttons must exist.",
        )
        self.assertTrue(
            self.template.active,
            "Template website_scroll_buttons.website_scroll_buttons must be active by default.",
        )

    def test_scroll_buttons_template_inheritance(self):
        """Verify that the template inherits website.layout properly."""
        layout_view = self.env.ref('website.layout', raise_if_not_found=False)
        self.assertIsNotNone(layout_view, "website.layout view must exist.")
        self.assertEqual(
            self.template.inherit_id,
            layout_view,
            "website_scroll_buttons template must inherit website.layout.",
        )

    def test_scroll_buttons_template_arch_elements(self):
        """Verify that scroll to top and bottom elements exist in the view architecture."""
        arch = self.template.arch
        self.assertIn(
            'website_scroll_buttons',
            arch,
            "Template arch must include 'website_scroll_buttons' class.",
        )
        self.assertIn(
            'scroll_to_bottom',
            arch,
            "Template arch must include 'scroll_to_bottom' button.",
        )
        self.assertIn(
            'scroll_to_top',
            arch,
            "Template arch must include 'scroll_to_top' button.",
        )

    def test_scroll_buttons_assets_declared(self):
        """Verify that JavaScript and CSS assets are declared in the module manifest."""
        manifest = get_manifest('website_scroll_buttons')
        self.assertTrue(manifest, "Module manifest must be accessible.")
        frontend_assets = manifest.get('assets', {}).get('web.assets_frontend', [])
        js_path = 'website_scroll_buttons/static/src/js/scroll_button.js'
        css_path = 'website_scroll_buttons/static/src/css/scroll_button.css'
        self.assertIn(js_path, frontend_assets, f"Frontend assets must include {js_path}.")
        self.assertIn(css_path, frontend_assets, f"Frontend assets must include {css_path}.")

