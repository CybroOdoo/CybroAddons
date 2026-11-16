###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
###############################################################################
from unittest.mock import patch

from odoo.tests.common import HttpCase, TransactionCase, tagged

from odoo.addons.website_extra_social_media.controllers import (
    website_extra_social_media as social_media_controller_module,
)


class FakeRequest:

    def __init__(self, env):
        self.env = env
        self.redirect_calls = []

    def redirect(self, url, local=True):
        self.redirect_calls.append((url, local))
        return {'url': url, 'local': local}


@tagged('post_install', '-at_install')
class TestWebsiteExtraSocialMediaController(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = social_media_controller_module.WebsiteExtraSocialMedia()
        cls.config_parameter = cls.env['ir.config_parameter'].sudo()
        cls.social_values = {
            'instagram_link': 'https://instagram.example.com/company',
            'whatsapp_link': '919876543210',
            'github_link': 'https://github.example.com/company',
            'youtube_link': 'https://youtube.example.com/company',
            'google_plus_link': 'https://plus.example.com/company',
            'snapchat_link': 'https://snapchat.example.com/company',
            'flickr_link': 'https://flickr.example.com/company',
            'quora_link': 'https://quora.example.com/company',
            'pinterest_link': 'https://pinterest.example.com/company',
            'dribbble_link': 'https://dribbble.example.com/company',
            'tumblr_link': 'https://tumblr.example.com/company',
        }

    def setUp(self):
        super().setUp()
        for field_name, value in self.social_values.items():
            self.config_parameter.set_str(
                'website_extra_social_media.%s' % field_name, value,
            )
        self.fake_request = FakeRequest(self.env)

    def _call_redirect(self, platform):
        with patch.object(
            social_media_controller_module, 'request', self.fake_request,
        ):
            return self.controller.social_media_redirect.__wrapped__(
                self.controller, platform,
            )

    def test_public_json_route_returns_configured_values(self):
        with patch.object(
            social_media_controller_module, 'request', self.fake_request,
        ):
            values = self.controller.get_social_media_values.__wrapped__(
                self.controller,
            )

        self.assertEqual(values['instagram'], self.social_values['instagram_link'])
        self.assertEqual(values['whatsapp'], self.social_values['whatsapp_link'])
        self.assertEqual(values['tumblr'], self.social_values['tumblr_link'])

    def test_social_media_routes_redirect_to_configured_urls(self):
        for field_name, expected_url in self.social_values.items():
            platform = field_name.removesuffix('_link')
            if platform == 'whatsapp':
                expected_url = (
                    'https://api.whatsapp.com/send?phone='
                    + expected_url
                )

            with self.subTest(platform=platform):
                result = self._call_redirect(platform)
                self.assertEqual(result, {'url': expected_url, 'local': False})

    def test_unknown_platform_redirects_home(self):
        result = self._call_redirect('unknown')

        self.assertEqual(result, {'url': '/', 'local': False})

    def test_social_media_routes_redirect_home_when_not_configured(self):
        for field_name in self.social_values:
            platform = field_name.removesuffix('_link')
            self.config_parameter.set_str(
                'website_extra_social_media.%s' % field_name, False,
            )

            with self.subTest(platform=platform):
                result = self._call_redirect(platform)
                self.assertEqual(result, {'url': '/', 'local': False})

            self.config_parameter.set_str(
                'website_extra_social_media.%s' % field_name,
                self.social_values[field_name],
            )


@tagged('post_install', '-at_install')
class TestWebsiteExtraSocialMediaPublicEndpoint(HttpCase):
    """Ensure anonymous visitors can load the snippet's public settings."""

    def test_anonymous_request_gets_social_media_values(self):
        self.env['ir.config_parameter'].sudo().set_str(
            'website_extra_social_media.instagram_link',
            'https://instagram.example.com/company',
        )

        response = self.url_open(
            '/website/social_media/values',
            json=self.build_rpc_payload(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['result']['instagram'],
            'https://instagram.example.com/company',
        )


@tagged('post_install', '-at_install')
class TestWebsiteExtraSocialMediaSnippet(HttpCase):
    """Ensure snippet visibility logic and tours work properly for public visitors."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_view = cls.env['ir.ui.view'].create({
            'name': 'Test Extra Social Media Page',
            'type': 'qweb',
            'key': 'website_extra_social_media.test_snippet_page_view',
            'arch': """
                <t t-call="website.layout">
                    <div id="wrap">
                        <t t-call="website_extra_social_media.extra_social_media"/>
                    </div>
                </t>
            """,
        })
        cls.test_page = cls.env['website.page'].create({
            'name': 'Test Extra Social Media Page',
            'url': '/test-extra-social-media',
            'view_id': cls.test_view.id,
            'website_indexed': False,
            'is_published': True,
        })

    def setUp(self):
        super().setUp()
        config_param = self.env['ir.config_parameter'].sudo()
        config_param.set_str(
            'website_extra_social_media.instagram_link',
            'https://instagram.example.com/company',
        )
        config_param.set_str(
            'website_extra_social_media.github_link',
            False,
        )

    def test_snippet_page_render_http(self):
        """Ensure snippet renders properly on a website page via HTTP request."""
        response = self.url_open('/test-extra-social-media')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'snippet_extra_social_media', response.content)
        self.assertIn(b'extra_social_media_instagram', response.content)
        self.assertIn(b'extra_social_media_home', response.content)

    def test_snippet_visibility_tour(self):
        """Ensure snippet interaction properly displays configured links and hides unconfigured links."""
        self.start_tour(
            '/test-extra-social-media',
            'website_extra_social_media_visibility',
            login=None,
        )
