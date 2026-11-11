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
        result = self.make_jsonrpc_request('/get_dashboard_carousel', {})
        self.assertIsNotNone(result)

    def test_dashboard_carousel_data(self):
        """Test dashboard carousel response data."""
        result = self.make_jsonrpc_request('/get_dashboard_carousel', {})
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0]['caption'], 'Demo Caption')