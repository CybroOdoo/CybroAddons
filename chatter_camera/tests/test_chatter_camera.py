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
import base64
import io

from odoo.modules.module import get_manifest
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestChatterCamera(HttpCase):
    """Test case for chatter camera module: manifest assets, tours, and photo attachment upload."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Chatter Camera Partner',
            'email': 'chatter_camera_test@example.com',
        })
        # Minimal valid 1x1 JPEG bytes
        cls.dummy_jpeg_bytes = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
            b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
            b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342'
            b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4'
            b'\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
            b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'
        )
        cls.dummy_jpeg_base64 = base64.b64encode(cls.dummy_jpeg_bytes).decode('ascii')

    def test_01_assets_and_manifest_configuration(self):
        """Ensure chatter_camera frontend, unit test and tour assets are declared."""
        manifest = get_manifest('chatter_camera')
        self.assertTrue(manifest, "Manifest for chatter_camera should be loaded.")
        assets = manifest.get('assets', {})
        backend_assets = assets.get('web.assets_backend', [])
        expected_backend = [
            'chatter_camera/static/src/css/style.css',
            'chatter_camera/static/src/js/chatter_camera.js',
            'chatter_camera/static/src/xml/chatter_camera.xml',
        ]
        for asset in expected_backend:
            self.assertIn(asset, backend_assets, f"Asset {asset} must be in web.assets_backend")

        unit_test_assets = assets.get('web.assets_unit_tests', [])
        self.assertTrue(unit_test_assets, "web.assets_unit_tests must be declared for Hoot tests.")

        tour_assets = assets.get('web.assets_tests', [])
        self.assertTrue(tour_assets, "web.assets_tests must be declared for Tours.")

    def test_02_chatter_camera_tour(self):
        """Execute chatter_camera tour to verify Camera button and CameraDialog flow."""
        self.start_tour(
            f"/odoo/res.partner/{self.partner.id}",
            "chatter_camera_tour",
            login="admin",
        )

    def test_03_camera_photo_upload_endpoint(self):
        """Test attachment upload via /mail/attachment/upload matching CameraDialog uploadFile flow."""
        self.authenticate('admin', 'admin')
        with io.BytesIO(self.dummy_jpeg_bytes) as file_stream:
            response = self.url_open(
                "/mail/attachment/upload",
                {
                    "csrf_token": self.csrf_token(),
                    "thread_id": self.partner.id,
                    "thread_model": "res.partner",
                },
                files={"ufile": ("capture_1729000000000.jpeg", file_stream, "image/jpeg")},
            )
        self.assertEqual(response.status_code, 200, "Upload endpoint should return HTTP 200")
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner.id),
            ('name', '=', 'capture_1729000000000.jpeg'),
        ], limit=1)
        self.assertTrue(attachment, "Attachment created by camera upload flow should exist.")
        self.assertEqual(attachment.mimetype, 'image/jpeg')

    def test_04_chatter_message_with_captured_photo(self):
        """Test linking the camera capture attachment to chatter message."""
        attachment = self.env['ir.attachment'].create({
            'name': 'capture_test_message.jpeg',
            'type': 'binary',
            'datas': self.dummy_jpeg_base64,
            'res_model': 'res.partner',
            'res_id': self.partner.id,
            'mimetype': 'image/jpeg',
        })
        message = self.partner.message_post(
            body="Photo captured from camera",
            attachment_ids=[attachment.id],
        )
        self.assertTrue(message.id, "Chatter message should be posted.")
        self.assertIn(
            attachment, message.attachment_ids,
            "Posted message should contain the camera attachment",
        )
