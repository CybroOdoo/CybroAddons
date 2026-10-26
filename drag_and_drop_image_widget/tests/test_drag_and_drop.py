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
#############################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestDragAndDropImageWidget(common.TransactionCase):
    """Test cases for Drag and Drop Image Widget module installation."""

    def test_module_installed(self):
        """Verify that the module is installed in the database."""
        module = self.env['ir.module.module'].search([
            ('name', '=', 'drag_and_drop_image_widget'),
        ])
        self.assertTrue(
            module, "Module drag_and_drop_image_widget should be found"
        )
        self.assertEqual(
            module.state, 'installed', "Module state should be installed"
        )

    def test_assets_registered(self):
        """Verify that web.assets_backend bundle includes the module assets."""
        module_name = 'drag_and_drop_image_widget'
        manifest = self.env['ir.module.module'].get_module_info(module_name)
        assets = manifest.get('assets', {})
        backend_assets = assets.get('web.assets_backend', [])

        expected_assets = [
            'drag_and_drop_image_widget/static/src/scss/drag_and_drop.scss',
            'drag_and_drop_image_widget/static/src/js/drag_and_drop.js',
            'drag_and_drop_image_widget/static/src/xml/'
            'drag_and_drop_templates.xml',
        ]
        for asset in expected_assets:
            self.assertIn(
                asset,
                backend_assets,
                f"Asset {asset} should be registered in web.assets_backend"
            )

    def test_unit_test_assets_registered(self):
        """Verify that web.assets_unit_tests bundle includes test files."""
        module_name = 'drag_and_drop_image_widget'
        manifest = self.env['ir.module.module'].get_module_info(module_name)
        assets = manifest.get('assets', {})
        unit_test_assets = assets.get('web.assets_unit_tests', [])

        self.assertIn(
            'drag_and_drop_image_widget/static/tests/**/*',
            unit_test_assets,
            "Tests glob pattern should be registered in web.assets_unit_tests"
        )
