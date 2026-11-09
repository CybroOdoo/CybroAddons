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
class TestGeolocationMapWidget(common.TransactionCase):
    """Test cases for Geolocation Map Widget module metadata and asset configuration."""

    def test_module_installed(self):
        """Verify that the module is installed in the database."""
        module = self.env['ir.module.module'].search([
            ('name', '=', 'geolocation_map_widget'),
        ])
        self.assertTrue(
            module, "Module geolocation_map_widget should be found"
        )
        self.assertEqual(
            module.state, 'installed', "Module state should be installed"
        )

    def test_manifest_dependencies(self):
        """Verify that 'web' and 'base' are declared in manifest dependencies."""
        module_name = 'geolocation_map_widget'
        manifest = self.env['ir.module.module'].get_module_info(module_name)
        depends = manifest.get('depends', [])
        self.assertIn(
            'web', depends, "'web' must be declared in module depends"
        )
        self.assertIn(
            'base', depends, "'base' must be declared in module depends"
        )

    def test_assets_registered(self):
        """Verify that web.assets_backend bundle includes the module assets."""
        module_name = 'geolocation_map_widget'
        manifest = self.env['ir.module.module'].get_module_info(module_name)
        assets = manifest.get('assets', {})
        backend_assets = assets.get('web.assets_backend', [])

        expected_assets = [
            'geolocation_map_widget/static/lib/leaflet/leaflet.css',
            'geolocation_map_widget/static/src/css/geolocation_map.css',
            'geolocation_map_widget/static/src/js/geolocation_map.js',
            'geolocation_map_widget/static/src/xml/geolocation_map_templates.xml',
        ]
        for asset in expected_assets:
            self.assertIn(
                asset,
                backend_assets,
                f"Asset {asset} should be registered in web.assets_backend"
            )

    def test_unit_test_assets_registered(self):
        """Verify that web.assets_unit_tests bundle includes test files and libraries."""
        module_name = 'geolocation_map_widget'
        manifest = self.env['ir.module.module'].get_module_info(module_name)
        assets = manifest.get('assets', {})
        unit_test_assets = assets.get('web.assets_unit_tests', [])

        self.assertIn(
            'geolocation_map_widget/static/lib/leaflet/leaflet.js',
            unit_test_assets,
            "Leaflet JS should be registered in web.assets_unit_tests"
        )
        self.assertIn(
            'geolocation_map_widget/static/src/**/*',
            unit_test_assets,
            "Source glob should be registered in web.assets_unit_tests"
        )
        self.assertIn(
            'geolocation_map_widget/static/tests/**/*',
            unit_test_assets,
            "Unit tests glob should be registered in web.assets_unit_tests"
        )
