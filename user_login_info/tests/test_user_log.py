# -*- coding: utf-8 -*-
################################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
# pylint: disable=protected-access,no-name-in-module
"""Unit test suite for user_login_info module."""
from unittest.mock import MagicMock, patch

from odoo import SUPERUSER_ID, api
from odoo.orm.registry import Registry
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.user_login_info.controllers.login_info import ImageController



@tagged('post_install', '-at_install', 'user_login_info')
class TestUserLog(TransactionCase):
    """Test suite for user.log records and controller helper methods."""

    @classmethod
    def setUpClass(cls):
        """Prepare test user and sample image binary."""
        super().setUpClass()
        cls.sample_b64 = (
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z'
            '/D/PwAHAwL/qGeMxAAAAABJRU5ErkJggg=='
        )
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test Login User',
            'login': 'test_login_user',
            'email': 'test_login_user@cybrosys.com',
        })
        cls.admin_user = cls.env.ref('base.user_admin')

    def test_user_log_create_successful_login(self):
        """Verify user.log creation for authenticated user login."""
        log = self.env['user.log'].create({
            'user_id': self.test_user.id,
            'image': self.sample_b64,
            'secure': False,
        })
        self.assertEqual(log.user_id, self.test_user)
        self.assertFalse(log.secure)
        self.assertTrue(log.image)
        self.assertEqual(log.display_name, self.test_user.name)

    def test_user_log_create_unknown_user(self):
        """Verify user.log creation for unknown/failed login attempts."""
        log = self.env['user.log'].create({
            'image': self.sample_b64,
            'secure': True,
        })
        self.assertFalse(log.user_id)
        self.assertTrue(log.secure)
        self.assertTrue(log.image)

    def test_user_log_cascade_delete(self):
        """Verify user.log records cascade-delete when user is removed."""
        temp_user = self.env['res.users'].create({
            'name': 'Temporary Login User',
            'login': 'temp_login_user',
            'email': 'temp_login_user@cybrosys.com',
        })
        log = self.env['user.log'].create({
            'user_id': temp_user.id,
            'secure': False,
        })
        log_id = log.id
        temp_user.unlink()
        remaining = self.env['user.log'].search([('id', '=', log_id)])
        self.assertFalse(remaining)

    def test_controller_save_user_log_helper(self):
        """Verify ImageController._save_user_log creates records in DB."""
        db_name = self.env.cr.dbname

        # Test successful login log creation using committed admin user
        ImageController._save_user_log(
            db_name, self.admin_user.id, True, self.sample_b64
        )
        # Test failed login log creation
        ImageController._save_user_log(
            db_name, None, False, self.sample_b64
        )

        with Registry(db_name).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            admin_log = env['user.log'].search([
                ('user_id', '=', self.admin_user.id)
            ], limit=1)
            self.assertTrue(admin_log)
            self.assertFalse(admin_log.secure)
            self.assertTrue(admin_log.image)

            unknown_log = env['user.log'].search([
                ('secure', '=', True)
            ], limit=1)
            self.assertTrue(unknown_log)
            self.assertFalse(unknown_log.user_id)
            self.assertTrue(unknown_log.image)
            (admin_log | unknown_log).unlink()

    def test_controller_capture_frame_none(self):
        """Verify ImageController._capture_frame handles None gracefully."""
        res = ImageController._capture_frame(None)
        self.assertIsNone(res)

    def test_controller_open_camera_mock(self):
        """Verify ImageController._open_camera with open/closed video."""
        controller = ImageController()
        mock_video = MagicMock()
        mock_video.isOpened.return_value = True

        with patch('odoo.addons.user_login_info.controllers.login_info.cv2') \
                as mock_cv2:
            mock_cv2.VideoCapture.return_value = mock_video
            res = controller._open_camera()
            self.assertEqual(res, mock_video)

            mock_video.isOpened.return_value = False
            res_closed = controller._open_camera()
            self.assertIsNone(res_closed)

    def test_controller_capture_frame_mock(self):
        """Verify ImageController._capture_frame with successful frame."""
        controller = ImageController()
        mock_video = MagicMock()
        mock_video.read.return_value = (True, b'fake_frame')

        with patch(
            'odoo.addons.user_login_info.controllers.login_info.cv2'
        ) as mock_cv2:
            mock_buffer = MagicMock(tobytes=lambda: b'image_bytes')
            mock_cv2.imencode.return_value = (True, mock_buffer)
            res = controller._capture_frame(mock_video)
            self.assertTrue(res)

            mock_cv2.imencode.return_value = (False, None)
            res_fail = controller._capture_frame(mock_video)
            self.assertIsNone(res_fail)

    def test_controller_capture_thread_mock(self):
        """Verify ImageController._capture_thread full workflow."""
        controller = ImageController()
        mock_video = MagicMock()
        mock_video.isOpened.return_value = True

        with patch.object(
            controller, '_open_camera', return_value=mock_video
        ), patch.object(
            controller, '_capture_frame', return_value='base64str'
        ), patch.object(controller, '_save_user_log') as mock_save:
            controller._capture_thread(1, True, self.env.cr.dbname)
            mock_save.assert_called_once_with(
                self.env.cr.dbname, 1, True, 'base64str'
            )
            mock_video.release.assert_called_once()


    def test_controller_image_capture_mock(self):
        """Verify ImageController._image_capture thread dispatching."""
        controller = ImageController()
        mock_request = MagicMock()
        mock_request.session.db = self.env.cr.dbname
        mock_request.session.uid = 1
        mock_request.params = {'login_success': True}

        target = 'odoo.addons.user_login_info.controllers.login_info.request'
        with patch(target, mock_request), \
             patch('threading.Thread') as mock_thread:
            controller._image_capture()
            mock_thread.assert_called_once()
