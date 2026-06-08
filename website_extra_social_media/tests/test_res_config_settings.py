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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.settings = cls.env['res.config.settings']
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

    def test_get_social_media_values_returns_configured_values(self):
        values = self.settings.get_social_media_values()

        self.assertEqual(values, {
            'instagram': self.social_values['instagram_link'],
            'whatsapp': self.social_values['whatsapp_link'],
            'github': self.social_values['github_link'],
            'youtube': self.social_values['youtube_link'],
            'google_plus': self.social_values['google_plus_link'],
            'snapchat': self.social_values['snapchat_link'],
            'flickr': self.social_values['flickr_link'],
            'quora': self.social_values['quora_link'],
            'pinterest': self.social_values['pinterest_link'],
            'dribble': self.social_values['dribble_link'],
            'tumblr': self.social_values['tumblr_link'],
        })

    def test_get_social_media_values_returns_false_for_unset_values(self):
        self.config_parameter.set_param(
            'website_extra_social_media.instagram_link', False
        )

        values = self.settings.get_social_media_values()

        self.assertFalse(values['instagram'])
        self.assertEqual(values['whatsapp'], self.social_values['whatsapp_link'])
