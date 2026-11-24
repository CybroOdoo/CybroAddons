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
"""Unit tests for Auto Save Restrict."""
import os

from odoo.modules.module import get_manifest
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAutoSaveRestrict(TransactionCase):
    """Test suite for Auto Save Restrict web client extension."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and file paths."""
        super().setUpClass()
        cls.module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_01_manifest_and_metadata(self):
        """Verify manifest configuration and compliance."""
        manifest = get_manifest('auto_save_restrict')
        self.assertTrue(manifest, "Manifest for auto_save_restrict must load.")
        self.assertEqual(manifest.get('version'), '20.0.1.0.0')
        self.assertEqual(manifest.get('license'), 'LGPL-3')
        self.assertIn('web', manifest.get('depends', []))
        self.assertEqual(manifest.get('author'), 'Cybrosys Techno Solutions')

    def test_02_assets_declaration_and_files_exist(self):
        """Verify all declared JS assets exist on disk and are readable."""
        manifest = get_manifest('auto_save_restrict')
        assets = manifest.get('assets', {}).get('web.assets_backend', [])
        expected_assets = [
            'auto_save_restrict/static/src/js/form_controller.js',
            'auto_save_restrict/static/src/js/list_controller.js',
            'auto_save_restrict/static/src/js/list_renderer.js',
        ]
        for asset in expected_assets:
            self.assertIn(asset, assets, f"Asset {asset} must be declared in web.assets_backend.")
            rel_path = asset.replace('auto_save_restrict/', '')
            file_path = os.path.join(self.module_dir, rel_path)
            self.assertTrue(os.path.isfile(file_path), f"File {file_path} must exist on disk.")
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
            self.assertTrue(len(content) > 0, f"Asset {asset} must not be empty.")

    def test_03_js_patches_content(self):
        """Verify patch targets and confirmation dialog integration in JS files."""
        # Check FormController patch
        form_path = os.path.join(self.module_dir, 'static', 'src', 'js', 'form_controller.js')
        with open(form_path, encoding='utf-8') as f:
            form_code = f.read()
        self.assertIn('FormController', form_code)
        self.assertIn('SettingsConfirmationDialog', form_code)
        self.assertIn('_confirmSave', form_code)
        self.assertIn('Would you like to save your changes?', form_code)

        # Check ListController patch
        list_ctrl_path = os.path.join(self.module_dir, 'static', 'src', 'js', 'list_controller.js')
        with open(list_ctrl_path, encoding='utf-8') as f:
            list_ctrl_code = f.read()
        self.assertIn('ListController', list_ctrl_code)
        self.assertIn('SettingsConfirmationDialog', list_ctrl_code)
        self.assertIn('beforeLeave', list_ctrl_code)

        # Check ListRenderer patch
        list_ren_path = os.path.join(self.module_dir, 'static', 'src', 'js', 'list_renderer.js')
        with open(list_ren_path, encoding='utf-8') as f:
            list_ren_code = f.read()
        self.assertIn('ListRenderer', list_ren_code)
        self.assertIn('onGlobalClick', list_ren_code)

    def test_04_ir_asset_registration(self):
        """Verify assets are correctly included in the web.assets_backend bundle."""
        asset_paths = self.env['ir.asset']._get_asset_paths('web.assets_backend', {})  # pylint: disable=protected-access
        paths = [str(p[0]) for p in asset_paths]
        self.assertTrue(
            any('form_controller.js' in p for p in paths),
            "form_controller.js must be registered in web.assets_backend bundle.",
        )
        self.assertTrue(
            any('list_controller.js' in p for p in paths),
            "list_controller.js must be registered in web.assets_backend bundle.",
        )
        self.assertTrue(
            any('list_renderer.js' in p for p in paths),
            "list_renderer.js must be registered in web.assets_backend bundle.",
        )

    def test_05_views_retrieval_integrity(self):
        """Verify backend form and list view architectures load without error."""
        partner_views = self.env['res.partner'].get_views([
            (False, 'form'),
            (False, 'list'),
        ])
        self.assertIn('views', partner_views)
        self.assertIn('form', partner_views['views'])
        self.assertIn('list', partner_views['views'])
        self.assertTrue(partner_views['views']['form']['arch'])
        self.assertTrue(partner_views['views']['list']['arch'])
