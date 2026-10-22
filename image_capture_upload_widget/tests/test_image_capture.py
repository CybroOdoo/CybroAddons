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
import os
from xml.etree import ElementTree
from odoo.modules import get_module_path
from odoo.tests.common import HttpCase, TransactionCase, tagged

SAMPLE_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@tagged('post_install', '-at_install')
class TestImageCaptureViews(TransactionCase):
    """Test suite for Image Capture Upload Widget views, assets, and records."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Image Partner',
            'email': 'partner.test@example.com',
        })
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test Image User',
            'login': 'test_image_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def test_01_view_partner_form_inheritance(self):
        """Verify res.partner form view inherits image_1920 with capture_image widget."""
        view = self.env.ref(
            'image_capture_upload_widget.view_partner_form_inherit_capture_image',
            raise_if_not_found=False,
        )
        self.assertTrue(view, "Inherited view for res.partner should exist.")
        self.assertEqual(view.model, 'res.partner')
        self.assertIn('capture_image', view.arch)
        self.assertIn("image_1920", view.arch)

    def test_02_view_users_form_inheritance(self):
        """Verify res.users form view inherits image_1920 with capture_image widget."""
        view = self.env.ref(
            'image_capture_upload_widget.view_users_form_inherit_capture_image',
            raise_if_not_found=False,
        )
        self.assertTrue(view, "Inherited view for res.users should exist.")
        self.assertEqual(view.model, 'res.users')
        self.assertIn('capture_image', view.arch)
        self.assertIn("image_1920", view.arch)

    def test_03_partner_image_upload_save(self):
        """Verify partner image_1920 can be saved with base64 data."""
        self.partner.write({'image_1920': SAMPLE_BASE64})
        self.assertTrue(self.partner.image_1920, "Partner image_1920 should be saved.")

    def test_04_user_image_upload_save(self):
        """Verify user image_1920 can be saved with base64 data."""
        self.test_user.write({'image_1920': SAMPLE_BASE64})
        self.assertTrue(self.test_user.image_1920, "User image_1920 should be saved.")

    def test_05_assets_bundle_registration(self):
        """Verify backend assets, Hoot unit test assets, and tour assets are defined."""
        module_path = get_module_path('image_capture_upload_widget')
        self.assertTrue(module_path, "Module path should exist.")

        # Unit test files
        hoot_test_path = os.path.join(
            module_path, 'static', 'tests', 'unit', 'image_capture_widget.test.js'
        )
        self.assertTrue(os.path.exists(hoot_test_path), "Hoot unit test file must exist.")

        # Tour test files
        tour_test_path = os.path.join(
            module_path, 'static', 'tests', 'tours', 'image_capture_tour.js'
        )
        self.assertTrue(os.path.exists(tour_test_path), "Tour test file must exist.")

    def test_06_component_and_template_spec(self):
        """Verify template XML is namespaced and JS file conforms to coding standards."""
        module_path = get_module_path('image_capture_upload_widget')
        xml_path = os.path.join(module_path, 'static', 'src', 'xml', 'image_capture_templates.xml')
        self.assertTrue(os.path.exists(xml_path), "Template XML file must exist.")

        tree = ElementTree.parse(xml_path)
        root = tree.getroot()
        templates = [el.attrib.get('t-name') for el in root.iter() if 't-name' in el.attrib]
        self.assertIn(
            'image_capture_upload_widget.CaptureImage',
            templates,
            "Template name should be properly namespaced as 'image_capture_upload_widget.CaptureImage'.",
        )

        js_path = os.path.join(module_path, 'static', 'src', 'js', 'image_capture.js')
        with open(js_path, 'r', encoding='utf-8') as js_file:
            js_content = js_file.read()

        self.assertNotIn("/** @odoo-module **/", js_content, "Obsolete @odoo-module header must not be present.")
        self.assertNotIn("console.error", js_content, "Debug console.error calls must not be present.")
        self.assertIn("onClickOpenCamera", js_content, "Handler must use camelCase onClickOpenCamera.")
        self.assertIn("onClickCaptureImage", js_content, "Handler must use camelCase onClickCaptureImage.")
        self.assertIn("onClickSaveImage", js_content, "Handler must use camelCase onClickSaveImage.")
        self.assertIn('registry.category("fields").add("capture_image", imageCapture);', js_content)
        self.assertNotIn('registry.category("fields").add("image_capture", imageCapture);', js_content)


@tagged('post_install', '-at_install')
class TestImageCaptureTour(HttpCase):
    """Browser tour test exercising Image Capture Upload Widget in client."""

    def test_image_capture_widget_tour(self):
        """Start browser tour and verify image capture widget interactive flow."""
        self.start_tour('/odoo/res.partner/new', 'image_capture_tour', login='admin')
