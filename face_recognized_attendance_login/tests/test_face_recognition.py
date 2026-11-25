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
from odoo.tests.common import HttpCase, tagged

# 1x1 transparent PNG image encoded in Base64 (string representation for Odoo 20 Binary fields)
SAMPLE_PNG_BASE64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='


@tagged('post_install', '-at_install')
class TestFaceRecognizedAttendance(HttpCase):
    """Test suite for Face Recognized Attendance Login module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.kiosk_token = 'test_kiosk_face_token_secure'
        cls.company.attendance_kiosk_key = cls.kiosk_token
        cls.company.attendance_kiosk_use_pin = False

        cls.department = cls.env['hr.department'].create({
            'name': 'Test Research & Development',
            'company_id': cls.company.id,
        })

        # Employee WITH face image
        cls.employee_with_image = cls.env['hr.employee'].create({
            'name': 'Face Verified Employee',
            'company_id': cls.company.id,
            'department_id': cls.department.id,
            'image_1920': SAMPLE_PNG_BASE64,
            'pin': '1234',
        })

        # Employee WITHOUT face image
        cls.employee_without_image = cls.env['hr.employee'].create({
            'name': 'No Photo Employee',
            'company_id': cls.company.id,
            'department_id': cls.department.id,
            'image_1920': False,
        })

    def test_01_get_image_with_valid_kiosk_token(self):
        """Test /get_image returns image data and face token when valid kiosk token is provided."""
        response = self.make_jsonrpc_request(
            '/get_image',
            params={
                'employee_id': self.employee_with_image.id,
                'token': self.kiosk_token,
            }
        )
        self.assertTrue(response, "Expected non-empty response for employee with photo and valid token")
        self.assertIsInstance(response, dict, "Response must be a dictionary with image and face_token")
        self.assertIn('image', response)
        self.assertIn('face_token', response)

        # Validate that image decodes into binary data
        decoded_bytes = base64.b64decode(response['image'])
        self.assertTrue(len(decoded_bytes) > 0, "Decoded image bytes should not be empty")
        self.assertTrue(bool(response['face_token']), "Face token must be generated")

    def test_02_get_image_without_valid_kiosk_token(self):
        """Test /get_image returns False when accessed with an invalid or missing kiosk token."""
        response = self.make_jsonrpc_request(
            '/get_image',
            params={
                'employee_id': self.employee_with_image.id,
                'token': 'unauthorized_fake_token',
            }
        )
        self.assertFalse(response, "Public request with invalid token must be denied to prevent image leaks")

    def test_03_get_image_without_photo(self):
        """Test /get_image returns False when an employee has no photo uploaded."""
        response = self.make_jsonrpc_request(
            '/get_image',
            params={
                'employee_id': self.employee_without_image.id,
                'token': self.kiosk_token,
            }
        )
        self.assertFalse(response, "Expected False for an employee without image (SVG initial avatar filtered out)")

    def test_04_get_image_non_existent_employee(self):
        """Test /get_image returns False when passing a non-existent employee ID."""
        response = self.make_jsonrpc_request(
            '/get_image',
            params={
                'employee_id': 9999999,
                'token': self.kiosk_token,
            }
        )
        self.assertFalse(response, "Expected False for a non-existent employee ID")

    def test_05_manual_selection_blocked_without_face_token(self):
        """Test /hr_attendance/manual_selection is blocked server-side if face token is missing."""
        # Initial check out state
        self.assertEqual(self.employee_with_image.attendance_state, 'checked_out')

        # Try to bypass face recognition by calling manual_selection without face_token
        response = self.make_jsonrpc_request(
            '/hr_attendance/manual_selection',
            params={
                'token': self.kiosk_token,
                'employee_id': self.employee_with_image.id,
                'pin_code': False,
            }
        )
        # Server must reject check-in without valid face verification token
        self.assertFalse(response, "Calling manual_selection without face_token must be blocked")
        self.assertEqual(
            self.employee_with_image.attendance_state,
            'checked_out',
            "Employee must remain checked out when face verification token is missing"
        )

    def test_06_manual_selection_allowed_with_valid_face_token(self):
        """Test complete flow: /get_image issues face_token, enabling verified check-in & check-out."""
        # Step 1: Kiosk requests image and obtains signed face_token
        token_data = self.make_jsonrpc_request(
            '/get_image',
            params={
                'employee_id': self.employee_with_image.id,
                'token': self.kiosk_token,
            }
        )
        face_token = token_data.get('face_token')
        self.assertTrue(face_token, "Must obtain a valid face_token from /get_image")

        # Step 2: Client performs face match and completes check-in with face_token
        check_in_response = self.make_jsonrpc_request(
            '/hr_attendance/manual_selection',
            params={
                'token': self.kiosk_token,
                'employee_id': self.employee_with_image.id,
                'pin_code': False,
                'face_token': face_token,
            }
        )
        self.assertTrue(check_in_response, "Check-in must succeed with valid face_token")
        self.assertEqual(self.employee_with_image.attendance_state, 'checked_in')

        # Step 3: Check-out flow with new face_token
        out_token_data = self.make_jsonrpc_request(
            '/get_image',
            params={
                'employee_id': self.employee_with_image.id,
                'token': self.kiosk_token,
            }
        )
        check_out_response = self.make_jsonrpc_request(
            '/hr_attendance/manual_selection',
            params={
                'token': self.kiosk_token,
                'employee_id': self.employee_with_image.id,
                'pin_code': False,
                'face_token': out_token_data.get('face_token'),
            }
        )
        self.assertTrue(check_out_response, "Check-out must succeed with valid face_token")
        self.assertEqual(self.employee_with_image.attendance_state, 'checked_out')
