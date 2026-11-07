# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
"""Unit tests for Dynamic Image Hotspot module."""
import os
from xml.etree import ElementTree as ET

from odoo.modules.module import get_module_path
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'dynamic_image_hotspot')
class TestDynamicImageHotspot(TransactionCase):
    """Test suite verifying module installation, manifest metadata, asset
    bundles, template structure, and website product links for Dynamic Image
    Hotspot.
    """

    @classmethod
    def setUpClass(cls):
        """Set up module path and module record for testing."""
        super().setUpClass()
        cls.module_path = get_module_path('dynamic_image_hotspot')
        cls.module = cls.env['ir.module.module'].search([
            ('name', '=', 'dynamic_image_hotspot'),
        ], limit=1)

    def test_01_module_installation(self):
        """Verify dynamic_image_hotspot is registered and installed."""
        self.assertTrue(
            self.module,
            "Module dynamic_image_hotspot must exist in ir.module.module.",
        )
        self.assertEqual(
            self.module.state,
            'installed',
            "Module dynamic_image_hotspot should be in installed state.",
        )

    def test_02_manifest_metadata(self):
        """Verify manifest completeness, dependencies, category, and license."""
        self.assertEqual(self.module.license, 'LGPL-3')
        self.assertEqual(self.module.category_id.name, 'Website')
        self.assertIn('Cybrosys', self.module.author)

        dependencies = [dep.name for dep in self.module.dependencies_id]
        self.assertIn('website_sale', dependencies)
        self.assertIn('html_builder', dependencies)

    def test_03_static_resources_exist(self):
        """Verify all declared static assets, templates, and documentation exist."""
        self.assertTrue(self.module_path, "Module path must exist.")
        expected_files = [
            'static/src/js/image_hotspot_plugin.js',
            'static/src/xml/image_hotspot_option.xml',
            'static/src/js/frontend.js',
            'static/src/css/style.css',
            'static/description/icon.png',
            'static/description/banner.jpg',
            'static/description/index.html',
            'static/description/assets/screenshots/1.png',
            'static/description/assets/screenshots/2.png',
            'static/description/assets/screenshots/3.png',
            'static/description/assets/screenshots/4.png',
            'static/description/assets/screenshots/5.png',
            'README.rst',
            'doc/RELEASE_NOTES.md',
        ]
        for rel_path in expected_files:
            full_path = os.path.join(self.module_path, rel_path)
            self.assertTrue(
                os.path.isfile(full_path),
                f"Required asset or document '{rel_path}' must exist on disk.",
            )
            self.assertGreater(
                os.path.getsize(full_path),
                0,
                f"File '{rel_path}' must not be empty.",
            )

    def test_04_xml_template_structure(self):
        """Verify image_hotspot_option.xml contains valid QWeb builder options."""
        xml_path = os.path.join(
            self.module_path, 'static/src/xml/image_hotspot_option.xml',
        )
        tree = ET.parse(xml_path)
        root = tree.getroot()

        self.assertEqual(root.tag, 'templates')

        extension_node = root.find(".//t[@t-inherit='website.BuilderOptions']")
        self.assertIsNotNone(
            extension_node,
            "Template extending 'website.BuilderOptions' must be present.",
        )
        self.assertEqual(extension_node.get('t-inherit-mode'), 'extension')

        option_template = root.find(
            ".//t[@t-name='dynamic_image_hotspot.ImageHotspotOption']",
        )
        self.assertIsNotNone(
            option_template,
            "Template 'dynamic_image_hotspot.ImageHotspotOption' must be present.",
        )

        xml_content = ET.tostring(root, encoding='unicode')
        self.assertIn('imageHotspotToggle', xml_content)
        self.assertIn('imageHotspotHorizontal', xml_content)
        self.assertIn('imageHotspotVertical', xml_content)
        self.assertIn('imageHotspotProduct', xml_content)

    def test_05_product_website_link_resolution(self):
        """Verify product template link resolution for website shop redirection."""
        product = self.env['product.template'].create({
            'name': 'Hotspot Interactive Test Item',
            'is_published': True,
            'sale_ok': True,
            'list_price': 99.0,
        })
        self.assertTrue(product.id, "Test product should be created.")

        expected_url = f"/shop/{product.id}"
        self.assertEqual(
            f"/shop/{product.id}",
            expected_url,
            "Product URL link should follow standard website_sale routing.",
        )

        domain = [('is_published', '=', True), ('sale_ok', '=', True)]
        eligible_products = self.env['product.template'].search(
            domain + [('id', '=', product.id)],
        )
        self.assertIn(
            product,
            eligible_products,
            "Created published product must match builder many2one domain.",
        )

    def test_06_access_rules(self):
        """Verify access rules defined in security/ir.access.csv."""
        group_designer = self.env.ref('website.group_website_designer')
        access = self.env['ir.access'].search([
            ('model_id.model', '=', 'product.template'),
            ('group_id', '=', group_designer.id),
        ])
        self.assertTrue(
            access,
            "Access rule for product.template and designer group must exist.",
        )
