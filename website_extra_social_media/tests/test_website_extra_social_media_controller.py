# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

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
            'dribble_link': 'https://dribbble.example.com/company',
            'tumblr_link': 'https://tumblr.example.com/company',
        }

    def setUp(self):
        super().setUp()
        for field_name, value in self.social_values.items():
            self.config_parameter.set_param(
                'website_extra_social_media.%s' % field_name, value
            )
        self.fake_request = FakeRequest(self.env)

    def _call_route(self, route_method):
        with patch.object(
            social_media_controller_module, 'request', self.fake_request
        ):
            return route_method.__wrapped__(self.controller)

    def test_get_social_values_reads_config_settings_defaults(self):
        with patch.object(
            social_media_controller_module, 'request', self.fake_request
        ):
            values = self.controller._get_social_values()

        self.assertEqual(values['instagram_link'], self.social_values['instagram_link'])
        self.assertEqual(values['whatsapp_link'], self.social_values['whatsapp_link'])
        self.assertEqual(values['tumblr_link'], self.social_values['tumblr_link'])

    def test_social_media_routes_redirect_to_configured_urls(self):
        route_cases = [
            ('instagram', 'https://instagram.example.com/company'),
            ('github', 'https://github.example.com/company'),
            ('youtube', 'https://youtube.example.com/company'),
            ('google_plus', 'https://plus.example.com/company'),
            ('snapchat', 'https://snapchat.example.com/company'),
            ('flickr', 'https://flickr.example.com/company'),
            ('quora', 'https://quora.example.com/company'),
            ('pinterest', 'https://pinterest.example.com/company'),
            ('dribbble', 'https://dribbble.example.com/company'),
            ('tumblr', 'https://tumblr.example.com/company'),
        ]

        for method_name, expected_url in route_cases:
            with self.subTest(route=method_name):
                result = self._call_route(getattr(self.controller, method_name))

                self.assertEqual(result, {'url': expected_url, 'local': False})

    def test_whatsapp_route_redirects_to_api_chat_url(self):
        result = self._call_route(self.controller.whatsapp)

        self.assertEqual(result, {
            'url': 'https://api.whatsapp.com/send?phone=919876543210',
            'local': False,
        })

    def test_social_media_routes_redirect_home_when_not_configured(self):
        route_cases = [
            ('instagram', 'instagram_link'),
            ('whatsapp', 'whatsapp_link'),
            ('github', 'github_link'),
            ('youtube', 'youtube_link'),
            ('google_plus', 'google_plus_link'),
            ('snapchat', 'snapchat_link'),
            ('flickr', 'flickr_link'),
            ('quora', 'quora_link'),
            ('pinterest', 'pinterest_link'),
            ('dribbble', 'dribble_link'),
            ('tumblr', 'tumblr_link'),
        ]

        for method_name, field_name in route_cases:
            with self.subTest(route=method_name):
                self.config_parameter.set_param(
                    'website_extra_social_media.%s' % field_name, False
                )

                result = self._call_route(getattr(self.controller, method_name))

                self.assertEqual(result, {'url': '/', 'local': False})
                self.config_parameter.set_param(
                    'website_extra_social_media.%s' % field_name,
                    self.social_values[field_name],
                )
