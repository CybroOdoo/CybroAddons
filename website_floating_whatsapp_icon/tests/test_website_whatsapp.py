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
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWebsiteWhatsApp(HttpCase):
    """Test suite for WhatsApp Floating Icon in Website"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref('base.default_website', raise_if_not_found=False) or cls.env['website'].search([], limit=1)

    def test_01_sanitized_mobile_number_computation(self):
        """Test sanitization of mobile numbers to numeric digits only"""
        # Test number with formatting (+, spaces, hyphens, brackets)
        self.website.mobile_number = '+1 (555) 123-4567'
        self.assertEqual(
            self.website.sanitized_mobile_number,
            '15551234567',
            "Sanitized mobile number must contain digits only without symbols"
        )

        # Test another format with country code
        self.website.mobile_number = '+91 98765-43210'
        self.assertEqual(
            self.website.sanitized_mobile_number,
            '919876543210',
            "Sanitized mobile number should extract only numeric digits"
        )

        # Test empty / False value
        self.website.mobile_number = False
        self.assertFalse(
            self.website.sanitized_mobile_number,
            "Sanitized mobile number should be False when mobile_number is empty"
        )

        # Test string with no digits
        self.website.mobile_number = '   '
        self.assertFalse(
            self.website.sanitized_mobile_number,
            "Sanitized mobile number should be False when no digits are present"
        )

    def test_02_frontend_rendering_with_mobile_number(self):
        """Test frontend page rendering when mobile number is configured"""
        self.website.mobile_number = '+1 (555) 888-9999'
        response = self.url_open('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'cy_whatsapp_web',
            response.text,
            "WhatsApp floating button class should be rendered when number is set"
        )
        self.assertIn(
            'phone=15558889999',
            response.text,
            "Rendered link must include the sanitized digits in the query parameter"
        )
        self.assertIn(
            'rel="noopener noreferrer"',
            response.text,
            "Rendered link must include rel='noopener noreferrer' for security"
        )
        self.assertIn(
            'data-icon="oi_whatsapp"',
            response.text,
            "Rendered template must contain the WhatsApp icon markup"
        )

    def test_03_frontend_rendering_without_mobile_number(self):
        """Test frontend page does not render floating button when mobile number is empty"""
        self.website.mobile_number = False
        response = self.url_open('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            'cy_whatsapp_web',
            response.text,
            "WhatsApp floating button should not be rendered when mobile_number is empty"
        )
