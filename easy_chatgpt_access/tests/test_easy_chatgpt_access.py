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
from odoo.modules.module import get_manifest
from odoo.tests.common import HttpCase, tagged
from odoo.tools.misc import file_path


@tagged('post_install', '-at_install')
class TestEasyChatGPTAccess(HttpCase):
    """Test suite for Easy ChatGPT Access module."""

    def test_01_manifest_metadata(self):
        """Verify manifest completeness, version, license, and dependencies."""
        manifest = get_manifest('easy_chatgpt_access')
        self.assertTrue(manifest, "Manifest for easy_chatgpt_access must exist.")
        self.assertEqual(manifest.get('name'), 'Easy ChatGPT Access')
        self.assertEqual(manifest.get('version'), '20.0.1.0.0')
        self.assertEqual(manifest.get('license'), 'LGPL-3')
        self.assertIn('web', manifest.get('depends', []))
        self.assertIn('html_editor', manifest.get('depends', []))

    def test_02_assets_declaration(self):
        """Verify that all assets declared in web.assets_backend exist on disk."""
        manifest = get_manifest('easy_chatgpt_access')
        assets = manifest.get('assets', {}).get('web.assets_backend', [])
        self.assertTrue(assets, "Module must declare assets in web.assets_backend.")
        for asset in assets:
            path = file_path(asset)
            self.assertTrue(path, f"Declared asset file must exist on disk: {asset}")

    def test_03_backend_systray_rendering(self):
        """Verify that an authenticated user can access the backend."""
        self.authenticate('admin', 'admin')
        response = self.url_open('/odoo')
        self.assertEqual(response.status_code, 200, "Backend /odoo should load successfully.")

    def test_04_html_editor_generate_text_endpoint(self):
        """Verify the /html_editor/generate_text endpoint structure."""
        self.authenticate('admin', 'admin')
        response = self.url_open(
            '/html_editor/generate_text',
            data='{"jsonrpc": "2.0", "method": "call", "params": {"prompt": "Test", "conversation_history": []}}',
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn('jsonrpc', json_data)
        self.assertTrue('result' in json_data or 'error' in json_data)

