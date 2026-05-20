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
from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged('post_install', '-at_install')
class TestInstaFeedSnippetController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.profile = cls.env['insta.profile'].create({
            'name': 'Demo Profile',
            'username': 'demo_user',
        })
        cls.env['insta.post'].create({
            'name': 'Post 1',
            'caption': 'Demo Caption',
            'profile_id': cls.profile.id,
        })

    def test_homepage_load(self):
        """Test website homepage loads."""
        response = self.url_open('/')
        self.assertEqual(
            response.status_code,
            200
        )

    def test_dashboard_carousel_route(self):
        """Test dashboard carousel json route."""
        response = self.opener.post(
            'http://127.0.0.1:8019/get_dashboard_carousel',
            json={}
        )
        self.assertEqual(
            response.status_code,
            200
        )
        data = response.json()
        self.assertTrue(data)

    def test_dashboard_carousel_data(self):
        """Test dashboard carousel response data."""
        response = self.opener.post(
            'http://127.0.0.1:8019/get_dashboard_carousel',
            json={}
        )
        result = response.json()
        self.assertIn(
            'result',
            result
        )
        self.assertTrue(
            isinstance(result['result'], list)
        )