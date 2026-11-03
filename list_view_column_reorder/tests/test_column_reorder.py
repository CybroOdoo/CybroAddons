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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
from odoo.modules import get_module_path
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestListViewColumnReorder(TransactionCase):
    """Test suite for list_view_column_reorder module manifests, assets, and files."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mod_path = get_module_path('list_view_column_reorder')

    def test_01_module_path_exists(self):
        """Verify the module directory is properly discovered by Odoo."""
        self.assertTrue(self.mod_path, "list_view_column_reorder path should be resolved.")
        self.assertTrue(os.path.isdir(self.mod_path), "Module path must be a directory.")

    def test_02_manifest_assets_defined(self):
        """Verify __manifest__.py defines all necessary assets and bundles."""
        manifest_file = os.path.join(self.mod_path, '__manifest__.py')
        self.assertTrue(os.path.isfile(manifest_file), "__manifest__.py must exist.")

        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest_data = eval(f.read())

        self.assertEqual(manifest_data.get('name'), 'List View Column Drag & Drop')
        self.assertIn('web', manifest_data.get('depends', []))

        assets = manifest_data.get('assets', {})
        self.assertIn('web.assets_backend', assets)
        self.assertIn('web.assets_unit_tests', assets)

        backend_assets = assets['web.assets_backend']
        self.assertIn('list_view_column_reorder/static/src/js/list_renderer_patch.js', backend_assets)
        self.assertIn('list_view_column_reorder/static/src/js/list_controller_patch.js', backend_assets)
        self.assertIn('list_view_column_reorder/static/src/css/list_renderer.css', backend_assets)
        self.assertIn('list_view_column_reorder/static/src/xml/list_renderer.xml', backend_assets)

        unit_tests_assets = assets['web.assets_unit_tests']
        self.assertIn('list_view_column_reorder/static/tests/**/*', unit_tests_assets)

    def test_03_static_files_exist(self):
        """Verify that all source and test javascript/xml/css files exist."""
        required_files = [
            'static/src/js/list_renderer_patch.js',
            'static/src/js/list_controller_patch.js',
            'static/src/css/list_renderer.css',
            'static/src/xml/list_renderer.xml',
            'static/tests/list_renderer_patch.test.js',
            'static/tests/list_controller_patch.test.js',
        ]
        for rel_path in required_files:
            abs_path = os.path.join(self.mod_path, rel_path)
            self.assertTrue(
                os.path.isfile(abs_path),
                f"Required static file does not exist: {rel_path}"
            )
