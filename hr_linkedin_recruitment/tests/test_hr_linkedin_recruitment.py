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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields
from odoo.addons.hr_linkedin_recruitment.controller.hr_linkedin_recruitment import LinkedinSocial


class TestAuthOauthProvider(TransactionCase):

    def test_client_secret_field(self):
        """Test that the client_secret field can be set on auth.oauth.provider."""
        provider = self.env['auth.oauth.provider'].create({
            'name': 'Test LinkedIn Provider',
            'auth_endpoint': 'https://example.com/auth',
            'validation_endpoint': 'https://example.com/validate',
            'body': 'Test Provider',
            'scope': 'test_scope',
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
        })
        self.assertEqual(provider.client_secret, 'test_client_secret')


class TestResConfigSettings(TransactionCase):

    def test_set_and_get_values(self):
        """Test setting and getting LinkedIn credentials via res.config.settings."""
        admin_user = self.env.ref('base.user_admin')
        config = self.env['res.config.settings'].with_user(admin_user).create({
            'li_username': 'test_user@linkedin.com',
            'li_password': 'super_secret_password',
        })
        config.set_values()

        # Check values are stored in ir.config_parameter
        username_param = self.env['ir.config_parameter'].sudo().get_param('recruitment.li_username')
        password_param = self.env['ir.config_parameter'].sudo().get_param('recruitment.li_password')
        self.assertEqual(username_param, 'test_user@linkedin.com')
        self.assertEqual(password_param, 'super_secret_password')

        # Retrieve values via get_values
        retrieved_config = self.env['res.config.settings'].with_user(admin_user).create({})
        values = retrieved_config.get_values()
        self.assertEqual(values.get('li_username'), 'test_user@linkedin.com')
        self.assertEqual(values.get('li_password'), 'super_secret_password')


class TestHrJob(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Find or create LinkedIn provider
        cls.provider = cls.env.ref('hr_linkedin_recruitment.provider_linkedin')
        cls.provider.write({
            'client_id': 'real_client_id',
            'client_secret': 'real_client_secret'
        })
        # Create a Job position for testing
        cls.job = cls.env['hr.job'].create({
            'name': 'Python Developer',
        })

    def test_get_linkedin_post_redirect_uri(self):
        """Test redirect URI generation."""
        uri = self.job._get_linkedin_post_redirect_uri()
        self.assertIn('/linkedin/redirect', uri)

    def test_share_linkedin_success(self):
        """Test that share_linkedin returns the proper action and sets is_comments."""
        action = self.job.share_linkedin()
        self.assertTrue(self.job.is_comments)
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertIn('https://www.linkedin.com/oauth/v2/authorization', action.get('url'))
        self.assertIn('client_id=real_client_id', action.get('url'))
        self.assertIn('state=%d' % self.job.id, action.get('url'))

    def test_share_linkedin_missing_credentials(self):
        """Test that ValidationError is raised when credentials are missing."""
        self.provider.write({
            'client_id': False,
            'client_secret': False
        })
        with self.assertRaises(ValidationError):
            self.job.share_linkedin()

    @patch('requests.request')
    def test_share_request(self, mock_request):
        """Test share_request method wraps requests.request properly."""
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        res = self.job.share_request('POST', 'https://api.linkedin.com', 'test_token', {'key': 'val'})
        mock_request.assert_called_once_with(
            'POST', 'https://api.linkedin.com',
            data={'key': 'val'},
            params={'oauth2_access_token': 'test_token'},
            headers={'x-li-format': 'json', 'Content-Type': 'application/json'},
            timeout=60
        )
        self.assertEqual(res, mock_response)

    @patch('requests.request')
    def test_get_urn(self, mock_request):
        """Test get_urn method wraps requests.request properly."""
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        res = self.job.get_urn('GET', 'https://api.linkedin.com/me', 'test_token')
        mock_request.assert_called_once_with(
            'GET', 'https://api.linkedin.com/me',
            params={'oauth2_access_token': 'test_token'},
            headers={'x-li-format': 'json', 'Content-Type': 'application/json'},
            timeout=60
        )
        self.assertEqual(res, mock_response)

    @patch('requests.request')
    def test_likes_comments(self, mock_request):
        """Test likes_comments method parses responses and creates comment records."""
        # Set access token in format: token+urn
        self.job.write({'access_token': 'mocked_token+mocked_urn'})

        # Setup mocked responses for:
        # 1. Social actions (likes and comments counts)
        # 2. Comments detail
        mock_response_social = MagicMock()
        mock_response_social.json.return_value = {
            'likesSummary': {'totalLikes': 42},
            'commentsSummary': {'aggregatedTotalComments': 7}
        }
        mock_response_comments = MagicMock()
        mock_response_comments.json.return_value = {
            'elements': [
                {
                    'id': 'comment_id_1',
                    'message': {'text': 'Nice job post!'}
                },
                {
                    'id': 'comment_id_2',
                    'message': {'text': 'Interested.'}
                }
            ]
        }
        mock_request.side_effect = [mock_response_social, mock_response_comments]

        self.job.likes_comments()

        self.assertTrue(self.job.like_comment)
        self.assertEqual(self.job.post_likes, 42)
        self.assertEqual(self.job.post_commands, 7)

        # Verify comments created
        comments = self.env['linkedin.comments'].search([('post_id', '=', self.job.id)])
        self.assertEqual(len(comments), 2)
        self.assertEqual(comments.mapped('comments_id'), ['comment_id_1', 'comment_id_2'])
        self.assertEqual(comments.mapped('linkedin_comments'), ['Nice job post!', 'Interested.'])

    def test_user_response_commends(self):
        """Test that user_response_commends returns action window with correct domain."""
        action = self.job.user_response_commends()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'linkedin.comments')
        self.assertEqual(action.get('domain'), [('post_id', '=', self.job.id)])

    @patch('requests.request')
    def test_view_shared_post(self, mock_request):
        """Test that view_shared_post redirects to the correct vanity name recent-activity URL."""
        self.job.write({'access_token': 'mocked_token+mocked_urn'})

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'vanityName': 'john-doe-recruitment'
        }
        mock_request.return_value = mock_response

        action = self.job.view_shared_post()
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertEqual(action.get('url'), 'https://www.linkedin.com/in/john-doe-recruitment/recent-activity/')


class TestLinkedinSocialController(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env.ref('hr_linkedin_recruitment.provider_linkedin')
        cls.provider.write({
            'client_id': 'real_client_id',
            'client_secret': 'real_client_secret'
        })
        cls.job = cls.env['hr.job'].create({
            'name': 'Odoo Developer',
        })
        # Set LinkedIn configurations
        cls.env['ir.config_parameter'].sudo().set_param('recruitment.li_username', 'test_user')
        cls.env['ir.config_parameter'].sudo().set_param('recruitment.li_password', 'test_pass')
        cls.controller = LinkedinSocial()

    @patch('requests.post')
    @patch('requests.request')
    def test_social_linkedin_callbacks_success(self, mock_request, mock_post):
        """Test social_linkedin_callbacks workflow with successful sharing (201)."""
        from odoo.http import Response
        mock_http_request = MagicMock()
        mock_http_request.env = self.env(context=dict(self.env.context, lang='en_US'))
        mock_http_request.context = {'lang': 'en_US'}
        mock_http_request.httprequest.url = 'http://localhost/linkedin/redirect?code=testcode&state=%d' % self.job.id
        mock_http_request.redirect.return_value = Response("redirecting...", status=302)

        # Mocking access token response
        mock_token_resp = MagicMock()
        mock_token_resp.json.return_value = {'access_token': 'access_token_123'}
        mock_post.return_value = mock_token_resp

        # Mocking URN get_urn response
        mock_urn_resp = MagicMock()
        mock_urn_resp.json.return_value = {'sub': 'person_urn_456'}

        # Mocking ugcPosts response (the sharing part)
        mock_share_resp = MagicMock()
        mock_share_resp.status_code = 201
        mock_share_resp.json.return_value = {'id': 'share_urn_789'}

        # side_effect order: get_urn (GET userinfo), share response (POST ugcPosts)
        mock_request.side_effect = [mock_urn_resp, mock_share_resp]

        with patch('odoo.http.request', new=mock_http_request), \
             patch('odoo.addons.hr_linkedin_recruitment.controller.hr_linkedin_recruitment.request', new=mock_http_request):
            # Call controller method
            self.controller.social_linkedin_callbacks()

        # Assertions
        self.assertEqual(self.job.access_token, 'access_token_123+share_urn_789')
        self.assertTrue(self.job.update_key)

    @patch('requests.post')
    @patch('requests.request')
    def test_social_linkedin_callbacks_validation_errors(self, mock_request, mock_post):
        """Test social_linkedin_callbacks validation errors for missing configuration."""
        mock_http_request = MagicMock()
        mock_http_request.env = self.env(context=dict(self.env.context, lang='en_US'))
        mock_http_request.context = {'lang': 'en_US'}
        mock_http_request.httprequest.url = 'http://localhost/linkedin/redirect?code=testcode&state=%d' % self.job.id

        mock_token_resp = MagicMock()
        mock_token_resp.json.return_value = {'access_token': 'access_token_123'}
        mock_post.return_value = mock_token_resp

        with patch('odoo.http.request', new=mock_http_request), \
             patch('odoo.addons.hr_linkedin_recruitment.controller.hr_linkedin_recruitment.request', new=mock_http_request):
            # 1. Test missing credentials in Provider
            self.provider.write({'client_id': False})
            with self.assertRaises(ValidationError):
                self.controller.social_linkedin_callbacks()
            self.provider.write({'client_id': 'real_client_id'})

            # 2. Test missing username in config
            self.env['ir.config_parameter'].sudo().set_param('recruitment.li_username', False)
            with self.assertRaises(ValidationError):
                self.controller.social_linkedin_callbacks()
            self.env['ir.config_parameter'].sudo().set_param('recruitment.li_username', 'test_user')

            # 3. Test missing password in config
            self.env['ir.config_parameter'].sudo().set_param('recruitment.li_password', False)
            with self.assertRaises(ValidationError):
                self.controller.social_linkedin_callbacks()

    @patch('requests.post')
    @patch('requests.request')
    def test_social_linkedin_callbacks_empty_job_description(self, mock_request, mock_post):
        """Test social_linkedin_callbacks when job description is empty."""
        mock_http_request = MagicMock()
        mock_http_request.env = self.env(context=dict(self.env.context, lang='en_US'))
        mock_http_request.context = {'lang': 'en_US'}
        mock_http_request.httprequest.url = 'http://localhost/linkedin/redirect?code=testcode&state=123'

        # Mocking access token response
        mock_token_resp = MagicMock()
        mock_token_resp.json.return_value = {'access_token': 'access_token_123'}
        mock_post.return_value = mock_token_resp

        # Mocking URN get_urn response
        mock_urn_resp = MagicMock()
        mock_urn_resp.json.return_value = {'sub': 'person_urn_456'}
        mock_request.return_value = mock_urn_resp

        mock_job = MagicMock(id=123)
        mock_job.name = False
        mock_job._get_linkedin_post_redirect_uri.return_value = 'http://localhost/linkedin/redirect'

        with patch('odoo.http.request', new=mock_http_request), \
             patch('odoo.addons.hr_linkedin_recruitment.controller.hr_linkedin_recruitment.request', new=mock_http_request), \
             patch.object(type(self.env['hr.job']), 'browse', return_value=mock_job):
            # Warning is a Python built-in exception raised in the controller
            with self.assertRaises(Warning):
                self.controller.social_linkedin_callbacks()

    @patch('requests.post')
    @patch('requests.request')
    def test_social_linkedin_callbacks_already_shared(self, mock_request, mock_post):
        """Test social_linkedin_callbacks when post is already shared (409)."""
        mock_http_request = MagicMock()
        mock_http_request.env = self.env(context=dict(self.env.context, lang='en_US'))
        mock_http_request.context = {'lang': 'en_US'}
        mock_http_request.httprequest.url = 'http://localhost/linkedin/redirect?code=testcode&state=%d' % self.job.id

        mock_token_resp = MagicMock()
        mock_token_resp.json.return_value = {'access_token': 'access_token_123'}
        mock_post.return_value = mock_token_resp

        mock_urn_resp = MagicMock()
        mock_urn_resp.json.return_value = {'sub': 'person_urn_456'}

        mock_share_resp = MagicMock()
        mock_share_resp.status_code = 409
        mock_share_resp.json.return_value = {'id': 'share_urn_789'}

        mock_request.side_effect = [mock_urn_resp, mock_share_resp]

        with patch('odoo.http.request', new=mock_http_request), \
             patch('odoo.addons.hr_linkedin_recruitment.controller.hr_linkedin_recruitment.request', new=mock_http_request):
            with self.assertRaises(Warning):
                self.controller.social_linkedin_callbacks()
