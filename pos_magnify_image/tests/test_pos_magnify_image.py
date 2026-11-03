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
import os
import xml.etree.ElementTree as ET

from odoo.modules.module import get_manifest, get_module_path
from odoo.tests.common import HttpCase, TransactionCase, tagged

# 1x1 transparent PNG in base64
TINY_PNG_BASE64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
    '+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
)


@tagged('post_install', '-at_install')
class TestPosMagnifyImage(TransactionCase):
    """Test suite covering static assets, templates, POS session lifecycle,
    and product image handling for pos_magnify_image."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module_name = 'pos_magnify_image'
        cls.mod_path = get_module_path(cls.module_name)

        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Magnify POS Config',
        })

        cls.product_with_image = cls.env['product.template'].create({
            'name': 'Magnify Test Product With Image',
            'available_in_pos': True,
            'image_1920': TINY_PNG_BASE64,
        })
        cls.product_no_image = cls.env['product.template'].create({
            'name': 'Magnify Test Product No Image',
            'available_in_pos': True,
        })

    def test_01_module_installed(self):
        """Verify that pos_magnify_image is installed and has valid dependencies."""
        module = self.env['ir.module.module'].search([
            ('name', '=', self.module_name),
        ], limit=1)
        self.assertTrue(module, "pos_magnify_image module record should exist.")
        self.assertEqual(
            module.state, 'installed',
            "pos_magnify_image should be installed in the database.",
        )

        manifest = get_manifest(self.module_name)
        self.assertIn(
            'point_of_sale', manifest.get('depends', []),
            "point_of_sale must be listed in module dependencies.",
        )

    def test_02_manifest_assets_declaration(self):
        """Verify that point_of_sale._assets_pos bundle contains all required files."""
        manifest = get_manifest(self.module_name)
        assets = manifest.get('assets', {})
        self.assertIn(
            'point_of_sale._assets_pos', assets,
            "Manifest must declare the 'point_of_sale._assets_pos' bundle.",
        )

        declared_files = assets['point_of_sale._assets_pos']
        expected_files = [
            'pos_magnify_image/static/src/css/pos_magnify_image.css',
            'pos_magnify_image/static/src/js/MagnifyProductPopup.js',
            'pos_magnify_image/static/src/xml/MagnifyProductPopup.xml',
            'pos_magnify_image/static/src/js/product_magnify_image.js',
            'pos_magnify_image/static/src/xml/product_magnify_image.xml',
        ]
        for expected in expected_files:
            self.assertIn(
                expected, declared_files,
                f"Asset {expected} should be declared in the bundle.",
            )

    def test_03_physical_asset_files_exist(self):
        """Ensure all declared static asset files physically exist and are non-empty."""
        self.assertTrue(
            self.mod_path and os.path.isdir(self.mod_path),
            "Module path should exist on filesystem.",
        )
        manifest = get_manifest(self.module_name)
        declared_files = manifest.get('assets', {}).get(
            'point_of_sale._assets_pos', [],
        )

        for asset_rel in declared_files:
            # Strip module prefix
            sub_path = asset_rel.removeprefix(f"{self.module_name}/")
            full_path = os.path.join(self.mod_path, sub_path)
            self.assertTrue(
                os.path.exists(full_path),
                f"Static file {full_path} must exist.",
            )
            self.assertGreater(
                os.path.getsize(full_path), 0,
                f"Static file {full_path} must not be empty.",
            )

    def test_04_assets_bundle_registered(self):
        """Verify that the assets are actively included in the POS bundle registry."""
        paths = [
            item[0]
            for item in self.env['ir.asset']._get_asset_paths(
                'point_of_sale._assets_pos', {},
            )
        ]
        expected_items = [
            '/pos_magnify_image/static/src/css/pos_magnify_image.css',
            '/pos_magnify_image/static/src/js/MagnifyProductPopup.js',
            '/pos_magnify_image/static/src/xml/MagnifyProductPopup.xml',
            '/pos_magnify_image/static/src/js/product_magnify_image.js',
            '/pos_magnify_image/static/src/xml/product_magnify_image.xml',
        ]
        for item in expected_items:
            self.assertIn(
                item, paths,
                f"{item} must be registered in the active 'point_of_sale._assets_pos' bundle.",
            )

    def test_05_xml_templates_structure(self):
        """Parse XML templates and verify Owl component tags and attributes."""
        # 1. product_magnify_image.xml
        card_xml_path = os.path.join(
            self.mod_path, 'static/src/xml/product_magnify_image.xml',
        )
        tree_card = ET.parse(card_xml_path)
        root_card = tree_card.getroot()
        self.assertEqual(root_card.tag, 'templates')

        extension_t = root_card.find('t')
        self.assertIsNotNone(extension_t)
        self.assertEqual(extension_t.get('t-name'), 'point_of_sale.ProductCard')
        self.assertEqual(extension_t.get('t-inherit'), 'point_of_sale.ProductCard')
        self.assertEqual(extension_t.get('t-inherit-mode'), 'extension')

        xpath_node = extension_t.find('xpath')
        self.assertIsNotNone(xpath_node)
        self.assertEqual(xpath_node.get('expr'), "//div[hasclass('product-img')]")
        self.assertEqual(xpath_node.get('position'), 'inside')

        magnify_div = xpath_node.find('div')
        self.assertIsNotNone(magnify_div)
        self.assertIn('pos-product-magnify', magnify_div.get('class', ''))
        self.assertIn('onProductMagnifyClick', magnify_div.get('t-on-click.stop', ''))

        # 2. MagnifyProductPopup.xml
        popup_xml_path = os.path.join(
            self.mod_path, 'static/src/xml/MagnifyProductPopup.xml',
        )
        tree_popup = ET.parse(popup_xml_path)
        root_popup = tree_popup.getroot()
        self.assertEqual(root_popup.tag, 'templates')

        popup_t = root_popup.find('t')
        self.assertIsNotNone(popup_t)
        self.assertEqual(popup_t.get('t-name'), 'MagnifyProductPopup')

        dialog_node = popup_t.find('Dialog')
        self.assertIsNotNone(dialog_node)
        self.assertEqual(dialog_node.get('title'), "'Product Image'")

        img_node = dialog_node.find('.//img')
        self.assertIsNotNone(img_node)
        self.assertIn('/web/image/product.template/', img_node.get('t-att-src', ''))
        self.assertIn('/image_1024', img_node.get('t-att-src', ''))

    def test_06_js_source_code_contract(self):
        """Verify JavaScript source files contain required component exports and methods."""
        # Check MagnifyProductPopup.js
        popup_js_path = os.path.join(
            self.mod_path, 'static/src/js/MagnifyProductPopup.js',
        )
        with open(popup_js_path, 'r', encoding='utf-8') as f:
            popup_js = f.read()

        self.assertIn('export class MagnifyProductPopup extends Component', popup_js)
        self.assertIn('onZoom(', popup_js)
        self.assertIn('startPan(', popup_js)
        self.assertIn('onPan(', popup_js)
        self.assertIn('stopPan(', popup_js)
        self.assertIn('applyTransform(', popup_js)

        # Check product_magnify_image.js
        patch_js_path = os.path.join(
            self.mod_path, 'static/src/js/product_magnify_image.js',
        )
        with open(patch_js_path, 'r', encoding='utf-8') as f:
            patch_js = f.read()

        self.assertIn('patch(ProductCard.prototype', patch_js)
        self.assertIn('onProductMagnifyClick', patch_js)
        self.assertIn('this.env.services.dialog.add(MagnifyProductPopup', patch_js)

    def test_07_css_styling_definitions(self):
        """Verify CSS contains styling for .pos-product-magnify icon and hover states."""
        css_path = os.path.join(
            self.mod_path, 'static/src/css/pos_magnify_image.css',
        )
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        self.assertIn('.pos-product-magnify', css_content)
        self.assertIn('position: absolute', css_content)
        self.assertIn('.pos-product-magnify:hover', css_content)

    def test_08_pos_session_initialization(self):
        """Verify that a POS session can be initialized cleanly with pos_magnify_image active."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
            'user_id': self.env.uid,
        })
        self.assertTrue(session, "POS session should be successfully created.")
        self.assertEqual(session.state, 'opening_control')

    def test_09_product_image_computation(self):
        """Verify product template image resolution and thumbnail generation."""
        self.assertTrue(
            self.product_with_image.image_1024,
            "Product with image_1920 must have a computed image_1024.",
        )
        self.assertFalse(
            self.product_no_image.image_1024,
            "Product without image_1920 should have false image_1024.",
        )


@tagged('post_install', '-at_install')
class TestPosMagnifyImageHttp(HttpCase):
    """HTTP endpoint test cases for product images rendered by MagnifyProductPopup."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_admin = cls.env.ref('base.user_admin')
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'HTTP Magnify Test Product',
            'available_in_pos': True,
            'image_1920': TINY_PNG_BASE64,
        })
        cls.product_tmpl_no_img = cls.env['product.template'].create({
            'name': 'HTTP Magnify Test Product Without Image',
            'available_in_pos': True,
        })

    def test_10_product_image_endpoint_with_image(self):
        """Verify that the /web/image/product.template/<id>/image_1024 route returns the image."""
        self.authenticate(self.user_admin.login, self.user_admin.login)
        url = f'/web/image/product.template/{self.product_tmpl.id}/image_1024'
        response = self.url_open(url)
        self.assertEqual(
            response.status_code, 200,
            f"Image URL {url} should return 200 OK.",
        )
        content_type = response.headers.get('Content-Type', '')
        self.assertTrue(
            content_type.startswith('image/'),
            f"Expected image/* content type, got {content_type}",
        )
        self.assertGreater(len(response.content), 0)

    def test_11_product_image_endpoint_fallback(self):
        """Verify that requesting /image_1024 on a product with no image returns a placeholder."""
        self.authenticate(self.user_admin.login, self.user_admin.login)
        url = f'/web/image/product.template/{self.product_tmpl_no_img.id}/image_1024'
        response = self.url_open(url)
        self.assertIn(
            response.status_code, [200, 301, 302, 303, 307],
            f"Image fallback for {url} should be valid HTTP status.",
        )
