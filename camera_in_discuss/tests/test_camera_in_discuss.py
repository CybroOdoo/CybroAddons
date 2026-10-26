# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
import os
import uuid

from odoo.modules.module import get_module_path
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestCameraInDiscuss(common.TransactionCase):
    """Test suite for Camera in Discuss module."""

    def setUp(self):
        super().setUp()
        self.module = self.env['ir.module.module'].search([
            ('name', '=', 'camera_in_discuss'),
        ])
        # Minimal 1x1 JPEG bytes
        self.sample_image_bytes = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
            b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4'
            b'\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
            b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'
        )

    def test_01_module_installation(self):
        """Verify that the module is loaded and marked as installed."""
        self.assertTrue(self.module, "Module camera_in_discuss should be found.")
        self.assertEqual(
            self.module.state,
            'installed',
            "Module camera_in_discuss should be in installed state.",
        )

    def test_02_static_resources_exist(self):
        """Verify all declared frontend assets and description files exist."""
        mod_path = get_module_path('camera_in_discuss')
        self.assertTrue(mod_path, "Module path for camera_in_discuss must exist.")
        required_files = [
            'static/src/discuss/camera/common/composer_patch.js',
            'static/src/discuss/camera/common/camera.css',
            'static/description/icon.png',
            'static/description/banner.jpg',
            'static/description/index.html',
        ]
        for rel_path in required_files:
            full_path = os.path.join(mod_path, rel_path)
            self.assertTrue(
                os.path.isfile(full_path),
                f"Required asset {rel_path} was not found on filesystem at {full_path}.",
            )

    def test_03_camera_attachment_post_in_channel(self):
        """Verify capturing and uploading a camera photo attachment to a discuss channel."""
        partner = self.env['res.partner'].create({
            'name': 'Test Discuss User',
            'email': 'test_discuss_user@example.com',
        })
        channel = self.env['discuss.channel'].create({
            'name': 'Camera Test Chat',
            'channel_type': 'chat',
            'channel_member_ids': [
                (0, 0, {'partner_id': self.env.user.partner_id.id}),
                (0, 0, {'partner_id': partner.id}),
            ],
        })

        file_name = f"camera_{uuid.uuid4()}.jpeg"
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'raw': self.sample_image_bytes,
            'mimetype': 'image/jpeg',
            'res_model': 'discuss.channel',
            'res_id': channel.id,
        })
        self.assertTrue(attachment.id, "Camera photo attachment should be created.")
        self.assertEqual(attachment.mimetype, 'image/jpeg')

        message = channel.message_post(
            body="Live camera capture",
            attachment_ids=[attachment.id],
            message_type='comment',
        )
        self.assertIn(attachment, message.attachment_ids)
        self.assertEqual(message.attachment_ids[0].name, file_name)

    def test_04_livechat_channel_compatibility(self):
        """Verify im_livechat dependency model availability."""
        livechat_channel = self.env['im_livechat.channel'].create({
            'name': 'Camera Support Livechat',
        })
        self.assertTrue(livechat_channel.id)
        self.assertEqual(livechat_channel.name, 'Camera Support Livechat')
