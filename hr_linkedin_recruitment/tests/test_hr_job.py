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
from unittest.mock import MagicMock, patch
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHrJob(TransactionCase):
    """Test cases for 'hr.job' model in hr_linkedin_recruitment."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.job = cls.env['hr.job'].create({
            'name': 'Software Engineer - Odoo',
        })
        cls.linkedin_provider = cls.env.ref(
            'hr_linkedin_recruitment.provider_linkedin', raise_if_not_found=False
        )
        if not cls.linkedin_provider:
            cls.linkedin_provider = cls.env['auth.oauth.provider'].create({
                'name': 'LinkedIn',
                'auth_endpoint': 'https://www.linkedin.com/oauth/v2/authorization',
            })

    def test__get_linkedin_post_redirect_uri(self):
        """Test _get_linkedin_post_redirect_uri constructs the expected callback URL."""
        redirect_uri = self.job._get_linkedin_post_redirect_uri()
        self.assertTrue(redirect_uri.endswith('/linkedin/redirect'))
        self.assertIn(self.job.get_base_url(), redirect_uri)

    test_get_linkedin_post_redirect_uri = test__get_linkedin_post_redirect_uri

    def test_share_linkedin(self):
        """Test share_linkedin returns authorization URL when credentials exist, and raises ValidationError when empty."""
        # 1. Test when credentials are set
        self.linkedin_provider.write({
            'client_id': 'test_client_id_123',
            'client_secret': 'test_client_secret_456',
        })
        self.job.is_comments = False
        action = self.job.share_linkedin()
        self.assertTrue(self.job.is_comments)
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertEqual(action.get('target'), 'self')
        url = action.get('url', '')
        self.assertTrue(url.startswith('https://www.linkedin.com/oauth/v2/authorization?'))
        self.assertIn('client_id=test_client_id_123', url)
        self.assertIn(f'state={self.job.id}', url)
        # 2. Test when credentials are empty -> raises ValidationError
        self.linkedin_provider.write({'client_id': False, 'client_secret': False})
        with self.assertRaises(ValidationError):
            self.job.share_linkedin()
        self.linkedin_provider.write({'client_id': 'test_client_id_123', 'client_secret': False})
        with self.assertRaises(ValidationError):
            self.job.share_linkedin()

    @patch('requests.request')
    def test_share_request(self, mock_request):
        """Test share_request executes request with proper payload, parameters and headers."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_request.return_value = mock_response
        res = self.job.share_request('POST', 'https://api.linkedin.com/v2/ugcPosts', 'token_123', '{"foo": "bar"}')
        self.assertEqual(res, mock_response)
        mock_request.assert_called_once_with(
            'POST',
            'https://api.linkedin.com/v2/ugcPosts',
            data='{"foo": "bar"}',
            params={'oauth2_access_token': 'token_123'},
            headers={'x-li-format': 'json', 'Content-Type': 'application/json'},
            timeout=60,
        )

    @patch('requests.request')
    def test_get_urn(self, mock_request):
        """Test get_urn sends GET/specified request with access token parameter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        res = self.job.get_urn('GET', 'https://api.linkedin.com/v2/userinfo', 'token_123')
        self.assertEqual(res, mock_response)
        mock_request.assert_called_once_with(
            'GET',
            'https://api.linkedin.com/v2/userinfo',
            params={'oauth2_access_token': 'token_123'},
            headers={'x-li-format': 'json', 'Content-Type': 'application/json'},
            timeout=60,
        )

    def test_user_response_like(self):
        """Test user_response_like returns None when no access token."""
        self.job.write({'access_token': False})
        res = self.job.user_response_like()
        self.assertIsNone(res)

    def test_user_response_like_with_token(self):
        """Test user_response_like calls likes_comments when access_token is set."""
        self.job.write({'access_token': 'test_token+urn:li:share:12345'})
        with patch.object(type(self.job), 'likes_comments') as mock_likes_comments:
            res = self.job.user_response_like()
            self.assertIsNone(res)
            mock_likes_comments.assert_called_once()

    @patch('requests.request')
    def test_likes_comments(self, mock_request):
        """Test likes_comments fetches social actions and creates linkedin.comments."""
        self.job.write({
            'access_token': 'test_token+urn:li:share:12345'
        })
        # Two requests are made:
        # 1. GET socialActions
        # 2. GET socialActions/.../comments
        resp_social = MagicMock()
        resp_social.json.return_value = {
            'likesSummary': {'totalLikes': 42},
            'commentsSummary': {'aggregatedTotalComments': 5},
        }
        resp_comments = MagicMock()
        resp_comments.json.return_value = {
            'elements': [
                {'id': 'comment_1', 'message': {'text': 'Awesome position!'}},
                {'id': 'comment_2', 'message': {'text': 'Applied!'}},
            ]
        }
        mock_request.side_effect = [resp_social, resp_comments]
        self.job.likes_comments()
        self.assertTrue(self.job.is_like_comment)
        self.assertEqual(self.job.post_likes, 42)
        self.assertEqual(self.job.post_commands, 5)
        created_comments = self.env['linkedin.comments'].search([('post_id', '=', self.job.id)])
        self.assertEqual(len(created_comments), 2)
        self.assertIn('comment_1', created_comments.mapped('comments_id'))
        self.assertIn('comment_2', created_comments.mapped('comments_id'))
        self.assertIn('Awesome position!', created_comments.mapped('linkedin_comments'))
        # Running again with existing comments should not create duplicates
        mock_request.side_effect = [resp_social, resp_comments]
        self.job.likes_comments()
        created_comments_after = self.env['linkedin.comments'].search([('post_id', '=', self.job.id)])
        self.assertEqual(len(created_comments_after), 2)

    def test_user_response_commends(self):
        """Test user_response_commends returns the action window pointing to linkedin.comments."""
        action = self.job.user_response_commends()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('target'), 'current')
        self.assertEqual(action.get('name'), 'Linkedin')
        self.assertEqual(action.get('view_mode'), 'list')
        self.assertEqual(action.get('res_model'), 'linkedin.comments')
        self.assertEqual(action.get('domain'), [('post_id', '=', self.job.id)])

    @patch('requests.request')
    def test_view_shared_post(self, mock_request):
        """Test view_shared_post fetches vanityName and returns act_url to recent activity."""
        self.job.write({
            'access_token': 'my_token+urn:li:share:999'
        })
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'vanityName': 'cybrosys-techno'}
        mock_request.return_value = mock_resp
        action = self.job.view_shared_post()
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertEqual(action.get('target'), 'self')
        self.assertEqual(action.get('url'), 'https://www.linkedin.com/in/cybrosys-techno/recent-activity/')
