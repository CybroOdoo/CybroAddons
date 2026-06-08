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
from unittest.mock import patch, MagicMock
from odoo.tests import TransactionCase, tagged
from odoo.addons.hr_linkedin_recruitment.controllers.hr_linkedin_recruitment import LinkedinSocial


@tagged('post_install', '-at_install')
class TestLinkedinSocial(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.job = cls.env['hr.job'].create({
            'name': 'Senior Python Developer',
        })
        cls.provider = cls.env.ref('hr_linkedin_recruitment.provider_linkedin')
        cls.provider.write({
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
        })
        cls.env['ir.config_parameter'].sudo().set_param('recruitment.li_username', 'test_user')
        cls.env['ir.config_parameter'].sudo().set_param('recruitment.li_password', 'test_password')

    def test_social_linkedin_callbacks(self):
        """Test the callback controller directly using mocked request environment."""

        class MockResponse:
            def __init__(self, json_data, status_code=200):
                self.json_data = json_data
                self.status_code = status_code
            def json(self):
                return self.json_data

        def mock_post(url, **kwargs):
            if 'accessToken' in url:
                return MockResponse({'access_token': 'mocked_access_token_123'})
            return MockResponse({})

        def mock_get_urn(method, url, access_token):
            return MockResponse({'sub': 'mocked_profile_urn'})

        def mock_request_api(method, url, **kwargs):
            if 'ugcPosts' in url:
                return MockResponse({'id': 'urn:li:share:abc123xyz'}, status_code=201)
            return MockResponse({})

        # Mock the Odoo Http Request ThreadLocal
        mock_request = MagicMock()
        mock_request.env = self.env
        mock_request.httprequest.url = f'https://example.com/linkedin/redirect?code=oauth_code_xyz&state={self.job.id}'
        
        import werkzeug
        mock_request.redirect.side_effect = lambda url, code=302: werkzeug.utils.redirect(url, code)

        controller = LinkedinSocial()

        # Patch requests and the request object in controllers module
        with patch('requests.post', side_effect=mock_post), \
             patch('odoo.addons.hr_linkedin_recruitment.models.hr_job.HrJobShare.get_urn', side_effect=mock_get_urn), \
             patch('requests.request', side_effect=mock_request_api), \
             patch('odoo.addons.hr_linkedin_recruitment.controllers.hr_linkedin_recruitment.request', mock_request), \
             patch('odoo.http.request', mock_request):
             
            # Call the callback controller method directly
            response = controller.social_linkedin_callbacks()
            
            # Verify the redirect action was triggered (usually 302 or 303 Redirect)
            self.assertIn(response.status_code, [302, 303])
            
            # Read state of job model to verify it was updated
            self.job.invalidate_recordset()
            self.assertEqual(self.job.access_token, 'mocked_access_token_123+urn:li:share:abc123xyz')
            self.assertTrue(self.job.update_key)
