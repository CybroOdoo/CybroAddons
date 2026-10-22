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
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestStickyPivot(HttpCase):
    """Test suite for Sticky Pivot View module."""

    def test_01_backend_assets_bundle(self):
        """Validate that backend assets and web client load without errors."""
        admin_user = self.env.ref('base.user_admin', raise_if_not_found=False) or self.env['res.users'].search([('share', '=', False)], limit=1)
        self.authenticate(admin_user.login, admin_user.login)
        response = self.url_open('/odoo')
        self.assertEqual(
            response.status_code, 200,
            "Backend web client should load successfully"
        )

    def test_02_css_asset_served(self):
        """Verify that the sticky pivot CSS is served correctly with scoped rules."""
        response = self.url_open('/sticky_pivot_view/static/src/css/main.css')
        self.assertEqual(response.status_code, 200, "CSS asset should be accessible")
        self.assertIn(
            '.o_pivot .cb_sticky',
            response.text,
            "CSS should contain scoped .o_pivot .cb_sticky rule"
        )
        self.assertIn(
            'position: sticky',
            response.text,
            "CSS should define sticky position"
        )
        self.assertIn(
            '.o_pivot tbody tr .text-nowrap',
            response.text,
            "CSS should contain scoped text-nowrap rule"
        )

    def test_03_xml_template_served(self):
        """Verify that the OWL template extension is served correctly."""
        response = self.url_open('/sticky_pivot_view/static/src/xml/pivot_template.xml')
        self.assertEqual(response.status_code, 200, "XML template should be accessible")
        self.assertIn(
            't-inherit="web.PivotRenderer"',
            response.text,
            "Template must inherit web.PivotRenderer"
        )
        self.assertIn(
            'add="cb_sticky"',
            response.text,
            "Template must add cb_sticky class attribute"
        )

    def test_04_qweb_bundle_compilation(self):
        """Validate that web.assets_backend bundle includes module assets."""
        bundle_css = self.env['ir.qweb']._get_asset_bundle(
            'web.assets_backend', css=True, js=False
        )
        self.assertTrue(
            bundle_css.stylesheets,
            "Backend CSS stylesheets bundle should exist"
        )
        css_content = bundle_css.css()
        self.assertTrue(
            css_content,
            "Generated bundle CSS content should not be empty"
        )
