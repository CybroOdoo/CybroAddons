# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
#
################################################################################
from unittest.mock import Mock, patch
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestInstaFeedSnippet(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.profile = cls.env['insta.profile'].create({
            'access_token': 'demo_token',
        })

    @patch(
        'odoo.addons.insta_feed_snippet.models.'
        'insta_profile.requests.get'
    )
    def test_action_fetch(self, mock_get):
        """Test instagram profile fetch."""
        page_response = Mock()
        page_response.json.return_value = {
            'data': [{
                'id': '100'
            }]
        }
        business_response = Mock()
        business_response.json.return_value = {
            'instagram_business_account': {
                'id': '200'
            }
        }
        profile_response = Mock()
        profile_response.json.return_value = {
            'id': '200',
            'name': 'Demo Profile',
            'username': 'demo_user',
            'profile_picture_url': 'http://test.com/image.jpg'
        }
        image_response = Mock()
        image_response.content = b'test_image'
        mock_get.side_effect = [
            page_response,
            business_response,
            profile_response,
            image_response,
        ]
        self.profile.action_fetch()
        self.assertEqual(
            self.profile.name,
            'Demo Profile'
        )
        self.assertEqual(
            self.profile.username,
            'demo_user'
        )
        self.assertEqual(
            self.profile.account_id,
            '200'
        )
        self.assertTrue(
            self.profile.profile_image_url
        )

    @patch(
        'odoo.addons.insta_feed_snippet.models.'
        'insta_profile.requests.get'
    )
    def test_action_fetch_error(self, mock_get):
        """Test instagram profile fetch error."""
        error_response = Mock()
        error_response.json.return_value = {
            'error': {
                'message': 'Invalid Token'
            }
        }
        mock_get.return_value = error_response
        with self.assertRaises(UserError):
            self.profile.action_fetch()

    @patch(
        'odoo.addons.insta_feed_snippet.models.'
        'insta_profile.requests.get'
    )
    def test_action_get_post(self, mock_get):
        """Test instagram post fetch."""
        self.profile.account_id = '200'
        media_response = Mock()
        media_response.json.return_value = {
            'data': [{
                'id': '300'
            }]
        }
        post_response = Mock()
        post_response.json.return_value = {
            'id': '300',
            'caption': 'Demo Caption',
            'media_type': 'IMAGE',
            'media_url': 'http://test.com/post.jpg'
        }
        image_response = Mock()
        image_response.content = b'post_image'
        mock_get.side_effect = [
            media_response,
            post_response,
            image_response,
        ]
        self.profile.action_get_post()
        post = self.env['insta.post'].search([
            ('name', '=', '300')
        ])
        self.assertTrue(post)
        self.assertEqual(
            post.caption,
            'Demo Caption'
        )
        self.assertEqual(
            post.profile_id,
            self.profile
        )
        self.assertTrue(
            post.post_image
        )

    @patch(
        'odoo.addons.insta_feed_snippet.models.'
        'insta_profile.requests.get'
    )
    def test_action_get_post_error(self, mock_get):
        """Test instagram post fetch error."""
        self.profile.account_id = '200'
        error_response = Mock()
        error_response.json.return_value = {
            'error': {
                'message': 'Access Denied'
            }
        }
        mock_get.return_value = error_response
        with self.assertRaises(UserError):
            self.profile.action_get_post()

    def test_insta_post_creation(self):
        """Test instagram post creation."""
        post = self.env['insta.post'].create({
            'name': '500',
            'caption': 'Test Caption',
            'profile_id': self.profile.id,
        })
        self.assertEqual(
            post.name,
            '500'
        )
        self.assertEqual(
            post.caption,
            'Test Caption'
        )
        self.assertEqual(
            post.profile_id,
            self.profile
        )
