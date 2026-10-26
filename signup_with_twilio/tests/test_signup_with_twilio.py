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
"""Unit tests for Mobile Signup with Twilio OTP."""
import time
from unittest.mock import MagicMock, patch
import odoo.http
from odoo.http import Response
from odoo.exceptions import UserError
from odoo.tests import common, tagged
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.signup_with_twilio.controllers.signup_with_twilio import (
    AuthSignupHome,
)


class MockResponse(Response):
    """Mock HTTP Response object returned by request.render."""

    def __init__(self, template, qcontext):
        super().__init__('rendered', status=200)
        self.template = template
        self.qcontext = qcontext or {}


@tagged('post_install', '-at_install')
class TestSignupWithTwilio(common.TransactionCase):
    """Test suite for Twilio configuration, OTP generation, and signup."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = AuthSignupHome()
        cls.env['ir.config_parameter'].sudo().set_str(
            'auth_signup.invitation_scope', 'b2c')
        cls.env['ir.config_parameter'].sudo().set_bool(
            'mail.use_call_server', True)
        cls.env['ir.config_parameter'].sudo().set_bool(
            'mail.use_twilio_rtc_servers', True)
        cls.env['ir.config_parameter'].sudo().set_str(
            'mail.twilio_account_sid', 'AC_TEST_ACCOUNT_SID')
        cls.env['ir.config_parameter'].sudo().set_str(
            'mail.twilio_account_token', 'TEST_AUTH_TOKEN')
        cls.env['ir.config_parameter'].sudo().set_str(
            'signup_with_twilio.twilio_from_number', '+15005550006')

    def _mock_request(self, session=None, params=None, method='GET'):
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.session = session if session is not None else {}
        mock_req.params = params if params is not None else {}
        mock_req.httprequest.method = method
        mock_req.csrf_token.return_value = 'mock_csrf'
        mock_req.render.side_effect = MockResponse
        return mock_req

    def test_res_config_settings_twilio_from_number(self):
        """Test field definition and config parameter for twilio_from_number."""
        self.env['ir.config_parameter'].sudo().set_str(
            'signup_with_twilio.twilio_from_number', '+12025550199')
        settings = self.env['res.config.settings'].create({})
        self.assertEqual(settings.twilio_from_number, '+12025550199')

    def test_send_otp_missing_credentials(self):
        """Test sending OTP fails when Twilio credentials are missing."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'mail.use_call_server', False)
        mock_req = self._mock_request()
        token = odoo.http.request_var.set(mock_req)
        try:
            with self.assertRaises(UserError):
                self.controller.web_send_otp(
                    country_code='1', mobile='2025550123')
        finally:
            odoo.http.request_var.reset(token)

    def test_send_otp_invalid_numbers(self):
        """Test sending OTP with non-digit country code or mobile fails."""
        mock_req = self._mock_request()
        token = odoo.http.request_var.set(mock_req)
        try:
            with self.assertRaises(UserError):
                self.controller.web_send_otp(
                    country_code='abc', mobile='2025550123')
            with self.assertRaises(UserError):
                self.controller.web_send_otp(
                    country_code='1', mobile='invalid')
        finally:
            odoo.http.request_var.reset(token)

    @patch('odoo.addons.signup_with_twilio.controllers.signup_with_twilio.'
           'Client')
    def test_send_otp_success_and_rate_limit(self, mock_client_cls):
        """Test OTP generation, session storage, and rate limiting."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = 'SM_MOCK_SID_123'
        mock_client.messages.create.return_value = mock_message
        mock_client_cls.return_value = mock_client

        session_dict = {}
        mock_req = self._mock_request(session=session_dict)
        token = odoo.http.request_var.set(mock_req)
        try:
            res = self.controller.web_send_otp(
                country_code='1', mobile='2025550123')
            self.assertEqual(res.get('status'), 'success')
            self.assertIn('signup_otp', session_dict)
            self.assertEqual(
                session_dict['signup_otp']['mobile'], '+12025550123')
            self.assertEqual(len(session_dict['signup_otp']['otp']), 4)
            self.assertTrue(mock_client.messages.create.called)

            # Test rate limiting within 30 seconds
            with self.assertRaises(UserError):
                self.controller.web_send_otp(
                    country_code='1', mobile='2025550123')
        finally:
            odoo.http.request_var.reset(token)

    def test_signup_mobile_post_missing_otp(self):
        """Test signup fails when OTP was not requested."""
        params = {
            'country_code': '1',
            'login_mobile': '2025550123',
            'sms_otp': '1234',
            'name': 'Test User',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }
        mock_req = self._mock_request(params=params, method='POST')
        token = odoo.http.request_var.set(mock_req)
        try:
            resp = self.controller.web_auth_signup_mobile(**params)
            ctx = resp.qcontext
            self.assertIn(
                'Please request a verification code',
                ctx.get('error', '')
            )
        finally:
            odoo.http.request_var.reset(token)

    def test_signup_mobile_post_expired_otp(self):
        """Test signup fails when OTP has expired (> 120 seconds)."""
        session_dict = {
            'signup_otp': {
                'otp': '4321',
                'mobile': '+12025550123',
                'timestamp': time.time() - 150,
            }
        }
        params = {
            'country_code': '1',
            'login_mobile': '2025550123',
            'sms_otp': '4321',
            'name': 'Test User',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }
        mock_req = self._mock_request(
            session=session_dict, params=params, method='POST')
        token = odoo.http.request_var.set(mock_req)
        try:
            resp = self.controller.web_auth_signup_mobile(**params)
            ctx = resp.qcontext
            self.assertIn('expired', ctx.get('error', '').lower())
        finally:
            odoo.http.request_var.reset(token)

    def test_signup_mobile_post_mismatched_phone(self):
        """Test signup fails when phone number doesn't match OTP request."""
        session_dict = {
            'signup_otp': {
                'otp': '4321',
                'mobile': '+12025550123',
                'timestamp': time.time(),
            }
        }
        params = {
            'country_code': '1',
            'login_mobile': '2025559999',
            'sms_otp': '4321',
            'name': 'Test User',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }
        mock_req = self._mock_request(
            session=session_dict, params=params, method='POST')
        token = odoo.http.request_var.set(mock_req)
        try:
            resp = self.controller.web_auth_signup_mobile(**params)
            ctx = resp.qcontext
            self.assertIn('does not match', ctx.get('error', '').lower())
        finally:
            odoo.http.request_var.reset(token)

    def test_signup_mobile_post_invalid_otp(self):
        """Test signup fails when submitted OTP does not match generated OTP."""
        session_dict = {
            'signup_otp': {
                'otp': '4321',
                'mobile': '+12025550123',
                'timestamp': time.time(),
            }
        }
        params = {
            'country_code': '1',
            'login_mobile': '2025550123',
            'sms_otp': '9999',
            'name': 'Test User',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }
        mock_req = self._mock_request(
            session=session_dict, params=params, method='POST')
        token = odoo.http.request_var.set(mock_req)
        try:
            resp = self.controller.web_auth_signup_mobile(**params)
            ctx = resp.qcontext
            self.assertIn('Invalid verification code', ctx.get('error', ''))
        finally:
            odoo.http.request_var.reset(token)

    def test_signup_mobile_post_success(self):
        """Test successful signup with valid OTP calls do_signup."""
        phone_number = '+12025550155'
        session_dict = {
            'signup_otp': {
                'otp': '5678',
                'mobile': phone_number,
                'timestamp': time.time(),
            }
        }
        params = {
            'country_code': '1',
            'login_mobile': '2025550155',
            'sms_otp': '5678',
            'name': 'Twilio Test User',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'signup_mobile': 'True',
        }
        mock_req = self._mock_request(
            session=session_dict, params=params, method='POST')
        token = odoo.http.request_var.set(mock_req)
        try:
            with patch.object(
                self.controller, 'do_signup'
            ) as mock_do_signup, patch.object(
                self.controller, 'web_login',
                return_value=Response('redirect_dashboard', status=200)
            ) as mock_login:
                res = self.controller.web_auth_signup_mobile(**params)
                self.assertEqual(res.status_code, 200)
                self.assertEqual(
                    res.get_data(as_text=True), 'redirect_dashboard')
                self.assertTrue(mock_do_signup.called)
                self.assertTrue(mock_login.called)
                self.assertNotIn('signup_otp', session_dict)
        finally:
            odoo.http.request_var.reset(token)

    def test_signup_mobile_post_already_registered(self):
        """Test signup fails when user with same mobile already exists."""
        phone_number = '+12025550999'
        partner = self.env['res.partner'].create({
            'name': 'Existing Mobile User',
            'phone': phone_number,
            'company_id': self.env.company.id,
        })
        self.env['res.users'].create({
            'partner_id': partner.id,
            'login': phone_number,
            'company_id': self.env.company.id,
        })
        session_dict = {
            'signup_otp': {
                'otp': '7777',
                'mobile': phone_number,
                'timestamp': time.time(),
            }
        }
        params = {
            'country_code': '1',
            'login_mobile': '2025550999',
            'sms_otp': '7777',
            'name': 'Duplicate User',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'signup_mobile': 'True',
        }
        mock_req = self._mock_request(
            session=session_dict, params=params, method='POST')
        token = odoo.http.request_var.set(mock_req)
        try:
            with patch.object(self.controller, 'do_signup', side_effect=SignupError):
                resp = self.controller.web_auth_signup_mobile(**params)
                ctx = resp.qcontext
                self.assertIn('already registered', ctx.get('error', '').lower())
        finally:
            odoo.http.request_var.reset(token)
