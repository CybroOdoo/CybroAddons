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
from odoo.tests import tagged
from odoo.tests.common import HttpCase, new_test_user
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestDiscussController(HttpCase):
    """Test cases for AttachmentController mail_attachment_upload override."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = new_test_user(
            cls.env,
            login='attachment_test_user',
            name='Attachment Test User',
            groups='base.group_user',
        )
        cls.channel = cls.env['discuss.channel'].create({
            'name': 'Test Channel',
            'channel_type': 'channel',
        })

    def _upload_file(self, filename, content, thread_id=None, thread_model="discuss.channel", is_pending=False):
        """Helper to invoke the /mail/attachment/upload HTTP endpoint."""
        if thread_id is None:
            thread_id = self.channel.id
        data = {
            'csrf_token': self.csrf_token(),
            'thread_id': thread_id,
            'thread_model': thread_model,
        }
        if is_pending:
            data['is_pending'] = 'true' if is_pending is True else is_pending

        return self.url_open(
            '/mail/attachment/upload',
            data=data,
            files={'ufile': (filename, content, 'application/octet-stream')},
        )

    def test_upload_non_existent_thread(self):
        """Test uploading an attachment to a non-existent thread raises 404."""
        self.authenticate('attachment_test_user', 'attachment_test_user')
        with mute_logger('odoo.http'):
            response = self._upload_file(
                'dummy.txt',
                b'Dummy text content',
                thread_id=99999999,
                thread_model='discuss.channel',
            )
        self.assertEqual(
            response.status_code,
            404,
            "Uploading to a non-existent thread should return HTTP 404.",
        )

    def test_upload_unrestricted_user(self):
        """Test that an unrestricted user can upload attachments without size error."""
        self.test_user.write({
            'set_restriction': False,
            'max_size': 0.0,
        })
        self.authenticate('attachment_test_user', 'attachment_test_user')

        # 2 MB content
        content = b'A' * (2 * 1024 * 1024)
        response = self._upload_file('large_allowed.txt', content)
        self.assertEqual(response.status_code, 200)

        res_json = response.json()
        self.assertNotIn(
            'size_error',
            res_json,
            "Unrestricted user should not receive a size error.",
        )
        self.assertIn('data', res_json)
        self.assertIn('attachment_id', res_json['data'])

        attachment = self.env['ir.attachment'].browse(res_json['data']['attachment_id'])
        self.assertTrue(attachment.exists())
        self.assertEqual(attachment.name, 'large_allowed.txt')

    def test_upload_restricted_user_within_limit(self):
        """Test that a restricted user can upload files within their allowed limit."""
        self.test_user.write({
            'set_restriction': True,
            'max_size': 1.0,  # 1 MB
        })
        self.authenticate('attachment_test_user', 'attachment_test_user')

        # 500 KB file (well within 1 MB)
        content = b'B' * (500 * 1024)
        response = self._upload_file('within_limit.txt', content)
        self.assertEqual(response.status_code, 200)

        res_json = response.json()
        self.assertNotIn(
            'size_error',
            res_json,
            "Attachment within the size limit should not trigger size_error.",
        )
        self.assertIn('data', res_json)
        self.assertIn('attachment_id', res_json['data'])

        attachment = self.env['ir.attachment'].browse(res_json['data']['attachment_id'])
        self.assertTrue(attachment.exists())
        self.assertEqual(attachment.file_size, len(content))

    def test_upload_restricted_user_exceeds_limit(self):
        """Test that an attachment exceeding user size limit is blocked with size_error."""
        self.test_user.write({
            'set_restriction': True,
            'max_size': 0.001,  # 0.001 MB = 1048.576 bytes
        })
        self.authenticate('attachment_test_user', 'attachment_test_user')

        # 2048 bytes (> 1048.576 bytes)
        content = b'C' * 2048
        response = self._upload_file('exceeded.txt', content)
        self.assertEqual(response.status_code, 200)

        res_json = response.json()
        self.assertIn(
            'size_error',
            res_json,
            "Exceeded file size should return a size_error key in response.",
        )
        self.assertIn('Attachment size cannot exceed 0.001 MB.', res_json['size_error'])
        self.assertNotIn(
            'data',
            res_json,
            "No attachment data should be returned when upload is rejected.",
        )

    def test_upload_restricted_user_zero_limit(self):
        """Test restriction with max_size set to 0.0 blocks any non-empty attachment."""
        self.test_user.write({
            'set_restriction': True,
            'max_size': 0.0,
        })
        self.authenticate('attachment_test_user', 'attachment_test_user')

        content = b'Non-empty file'
        response = self._upload_file('blocked.txt', content)
        self.assertEqual(response.status_code, 200)

        res_json = response.json()
        self.assertIn('size_error', res_json)
        self.assertIn('Attachment size cannot exceed 0.0 MB.', res_json['size_error'])

    def test_upload_is_pending_flag(self):
        """Test uploading attachment with is_pending sets placeholder values."""
        self.test_user.write({
            'set_restriction': False,
        })
        self.authenticate('attachment_test_user', 'attachment_test_user')

        content = b'Pending attachment content'
        response = self._upload_file('pending.txt', content, is_pending=True)
        self.assertEqual(response.status_code, 200)

        res_json = response.json()
        self.assertIn('data', res_json)
        attachment_id = res_json['data']['attachment_id']
        attachment = self.env['ir.attachment'].browse(attachment_id)

        self.assertEqual(
            attachment.res_model,
            'mail.compose.message',
            "is_pending uploads should associate with 'mail.compose.message'.",
        )
        self.assertEqual(
            attachment.res_id,
            0,
            "is_pending uploads should set res_id to 0.",
        )
