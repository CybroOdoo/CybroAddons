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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestHrJobShare(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.job = cls.env['hr.job'].create({
            'name': 'Python Developer',
            'access_token': 'my_bearer_token+urn:li:share:98765',
        })
        cls.provider = cls.env.ref('hr_linkedin_recruitment.provider_linkedin')

    def test_01_get_linkedin_post_redirect_uri(self):
        """Test _get_linkedin_post_redirect_uri returns redirect path."""
        uri = self.job._get_linkedin_post_redirect_uri()
        self.assertIn('/linkedin/redirect', uri)

    def test_02_share_linkedin_validation_error(self):
        """Test share_linkedin raises ValidationError if credentials are empty."""
        self.provider.write({
            'client_id': False,
            'client_secret': False,
        })
        with self.assertRaises(ValidationError):
            self.job.share_linkedin()

    def test_03_share_linkedin_success(self):
        """Test share_linkedin returns redirect action when credentials are set."""
        self.provider.write({
            'client_id': 'my_client_id',
            'client_secret': 'my_client_secret',
        })
        res = self.job.share_linkedin()
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertIn('https://www.linkedin.com/oauth/v2/authorization', res.get('url'))

    def test_04_share_request(self):
        """Test share_request sends API request and returns response."""
        with patch('requests.request') as mock_req:
            mock_req.return_value = 'mocked_response'
            res = self.job.share_request('POST', 'https://api.linkedin.com/share', 'token', {'msg': 'test'})
            mock_req.assert_called_once()
            self.assertEqual(res, 'mocked_response')

    def test_05_get_urn(self):
        """Test get_urn sends API verification request."""
        with patch('requests.request') as mock_req:
            mock_req.return_value = 'mocked_urn_response'
            res = self.job.get_urn('GET', 'https://api.linkedin.com/me', 'token')
            mock_req.assert_called_once()
            self.assertEqual(res, 'mocked_urn_response')

    def test_06_likes_comments(self):
        """Test likes_comments fetches counts and populates linkedin.comments."""
        # Clean any comments
        self.env['linkedin.comments'].search([]).unlink()

        # Mock responses for total likes/comments and details of comments
        class MockResponse:
            def __init__(self, json_data):
                self.json_data = json_data
            def json(self):
                return self.json_data

        def mock_request(method, url, **kwargs):
            if 'comments' in url:
                return MockResponse({
                    'elements': [
                        {
                            'id': 'comment_123',
                            'message': {'text': 'Awesome Job Opportunity!'}
                        }
                    ]
                })
            else:
                return MockResponse({
                    'likesSummary': {'totalLikes': 12},
                    'commentsSummary': {'aggregatedTotalComments': 5}
                })

        with patch('requests.request', side_effect=mock_request):
            self.job.likes_comments()
            self.assertTrue(self.job.is_like_comment)
            self.assertEqual(self.job.post_likes, 12)
            self.assertEqual(self.job.post_commands, 5)

            # Check comments creation
            comment = self.env['linkedin.comments'].search([('comments_id', '=', 'comment_123')])
            self.assertTrue(comment.exists())
            self.assertEqual(comment.linkedin_comments, 'Awesome Job Opportunity!')

    def test_07_user_response_commends(self):
        """Test user_response_commends action window definition."""
        res = self.job.user_response_commends()
        self.assertEqual(res.get('type'), 'ir.actions.act_window')
        self.assertEqual(res.get('res_model'), 'linkedin.comments')
        self.assertEqual(res.get('domain'), [('post_id', '=', self.job.id)])

    def test_08_view_shared_post(self):
        """Test view_shared_post handles URN activity URL generation."""
        class MockResponse:
            def json(self):
                return {'vanityName': 'john-doe-linkedin'}

        with patch('requests.request', return_value=MockResponse()):
            res = self.job.view_shared_post()
            self.assertEqual(res.get('type'), 'ir.actions.act_url')
            self.assertEqual(res.get('url'), 'https://www.linkedin.com/in/john-doe-linkedin/recent-activity/')
