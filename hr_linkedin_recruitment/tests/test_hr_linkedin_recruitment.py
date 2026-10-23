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
from contextlib import contextmanager
from unittest.mock import MagicMock, PropertyMock, patch
from werkzeug.utils import redirect as werkzeug_redirect

import odoo.http
from odoo.exceptions import UserError, ValidationError
from odoo.tests import HttpCase, tagged
from odoo.addons.hr_linkedin_recruitment.controllers.hr_linkedin_recruitment import LinkedinSocial


@contextmanager
def bound_mock_request(mock_request):
    """Context manager to bind mock request to odoo.http.request_var."""
    token = odoo.http.request_var.set(mock_request)
    try:
        yield mock_request
    finally:
        odoo.http.request_var.reset(token)


@tagged('post_install', '-at_install')
class TestHrLinkedinRecruitment(HttpCase):
    """Test cases for LinkedIn recruitment controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.job = cls.env['hr.job'].create({
            'name': 'Senior Python Developer',
        })
        cls.provider = cls.env.ref(
            'hr_linkedin_recruitment.provider_linkedin', raise_if_not_found=False
        )
        if not cls.provider:
            cls.provider = cls.env['auth.oauth.provider'].create({
                'name': 'LinkedIn',
                'auth_endpoint': 'https://www.linkedin.com/oauth/v2/authorization',
            })
        cls.controller = LinkedinSocial()

    def test_social_linkedin_callbacks(self):
        """Test social_linkedin_callbacks handles OAuth exchange, post creation, and validations."""
        # 1. Setup valid credentials
        self.provider.write({
            'client_id': 'valid_client_id_123',
            'client_secret': 'valid_client_secret_456',
        })
        self.env['ir.config_parameter'].sudo().set_str('recruitment.li_username', 'li_user_test')
        self.env['ir.config_parameter'].sudo().set_str('recruitment.li_password', 'li_pass_test')

        mock_httprequest = MagicMock()
        mock_httprequest.url = f'http://localhost:8069/linkedin/redirect?code=oauth_auth_code_123&state={self.job.id}'

        mock_req = MagicMock()
        mock_req.httprequest = mock_httprequest
        mock_req.env = self.env
        mock_req.redirect.side_effect = werkzeug_redirect

        with bound_mock_request(mock_req), \
             patch('requests.post') as mock_post, \
             patch('requests.request') as mock_request:

            # Mock accessToken response
            token_resp = MagicMock()
            token_resp.json.return_value = {'access_token': 'sample_access_token_xyz'}
            mock_post.return_value = token_resp

            # Mock get_urn call (via requests.request for userinfo)
            userinfo_resp = MagicMock()
            userinfo_resp.json.return_value = {'sub': 'linkedin_sub_id'}

            # Mock ugcPosts share response
            share_resp = MagicMock()
            share_resp.status_code = 201
            share_resp.json.return_value = {'id': 'urn:li:share:987654321'}

            mock_request.side_effect = [userinfo_resp, share_resp]

            result = self.controller.social_linkedin_callbacks()

            # Verify access_token and update_key updated on job
            self.job.invalidate_recordset(['access_token', 'update_key'])
            self.assertEqual(self.job.access_token, 'sample_access_token_xyz+urn:li:share:987654321')
            self.assertTrue(self.job.update_key)
            self.assertEqual(result.status_code, 302)
            self.assertIn(f'/odoo/hr.job/{self.job.id}', result.headers.get('Location'))

        # 2. Verify validation error when provider client_id is missing
        self.provider.write({'client_id': False})
        with bound_mock_request(mock_req), \
             patch('requests.post') as mock_post:
            token_resp = MagicMock()
            token_resp.json.return_value = {'access_token': 'sample_access_token_xyz'}
            mock_post.return_value = token_resp
            with self.assertRaises(ValidationError):
                self.controller.social_linkedin_callbacks()

        # 3. Verify validation error when li_username is missing
        self.provider.write({'client_id': 'valid_client_id_123'})
        self.env['ir.config_parameter'].sudo().set_str('recruitment.li_username', False)
        with bound_mock_request(mock_req), \
             patch('requests.post') as mock_post:
            token_resp = MagicMock()
            token_resp.json.return_value = {'access_token': 'sample_access_token_xyz'}
            mock_post.return_value = token_resp
            with self.assertRaises(ValidationError):
                self.controller.social_linkedin_callbacks()

        # 4. Verify validation error when li_password is missing
        self.env['ir.config_parameter'].sudo().set_str('recruitment.li_username', 'li_user_test')
        self.env['ir.config_parameter'].sudo().set_str('recruitment.li_password', False)
        with bound_mock_request(mock_req), \
             patch('requests.post') as mock_post:
            token_resp = MagicMock()
            token_resp.json.return_value = {'access_token': 'sample_access_token_xyz'}
            mock_post.return_value = token_resp
            with self.assertRaises(ValidationError):
                self.controller.social_linkedin_callbacks()

        # 5. Verify error handling for 404, 409, 500, and empty name
        self.env['ir.config_parameter'].sudo().set_str('recruitment.li_password', 'li_pass_test')
        for code, expected_error in [(404, "Resource does not exist."), (409, "Already shared."), (500, "Error! Check your connection.")]:
            with bound_mock_request(mock_req), \
                 patch('requests.post') as mock_post, \
                 patch('requests.request') as mock_request:
                mock_post.return_value.json.return_value = {'access_token': 'sample_token'}
                userinfo_resp = MagicMock()
                userinfo_resp.json.return_value = {'sub': 'sub_123'}
                err_resp = MagicMock()
                err_resp.status_code = code
                err_resp.json.return_value = {'id': 'urn:li:share:1'}
                mock_request.side_effect = [userinfo_resp, err_resp]
                with self.assertRaises(UserError):
                    self.controller.social_linkedin_callbacks()

        # 6. Verify empty job name raises UserError
        mock_httprequest.url = f'http://localhost:8069/linkedin/redirect?code=oauth_auth_code_123&state={self.job.id}'
        with bound_mock_request(mock_req), \
             patch('requests.post') as mock_post, \
             patch('requests.request') as mock_request, \
             patch.object(type(self.job), 'name', new_callable=PropertyMock, return_value=''):
            mock_post.return_value.json.return_value = {'access_token': 'sample_token'}
            userinfo_resp = MagicMock()
            userinfo_resp.json.return_value = {'sub': 'sub_123'}
            mock_request.side_effect = [userinfo_resp]
            with self.assertRaises(UserError):
                self.controller.social_linkedin_callbacks()
