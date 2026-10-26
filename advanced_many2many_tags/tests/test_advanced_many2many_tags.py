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
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAdvancedMany2ManyTags(TransactionCase):
    """Test cases for advanced_many2many_tags module installation and assets."""

    def test_module_state(self):
        """Verify the module is installed and state is installed."""
        module = self.env['ir.module.module'].search([
            ('name', '=', 'advanced_many2many_tags')
        ])
        self.assertTrue(module, "Module advanced_many2many_tags should be found")
        self.assertEqual(module.state, 'installed', "Module state should be installed")

    def test_assets_registered(self):
        """Verify that web.assets_backend bundle includes the module JS and XML assets."""
        manifest = module = self.env['ir.module.module'].get_module_info('advanced_many2many_tags')
        assets = manifest.get('assets', {})
        backend_assets = assets.get('web.assets_backend', [])

        expected_assets = [
            'advanced_many2many_tags/static/src/js/confirmation_dialog_view.js',
            'advanced_many2many_tags/static/src/js/many2many_tags_field.js',
            'advanced_many2many_tags/static/src/xml/many2many_tags_field.xml',
        ]
        for asset in expected_assets:
            self.assertIn(asset, backend_assets, f"Asset {asset} should be registered in web.assets_backend")

    def test_unit_test_assets_registered(self):
        """Verify that web.assets_unit_tests bundle includes the test files."""
        manifest = self.env['ir.module.module'].get_module_info('advanced_many2many_tags')
        assets = manifest.get('assets', {})
        unit_test_assets = assets.get('web.assets_unit_tests', [])

        self.assertIn(
            'advanced_many2many_tags/static/tests/**/*',
            unit_test_assets,
            "Tests glob pattern should be registered in web.assets_unit_tests"
        )
