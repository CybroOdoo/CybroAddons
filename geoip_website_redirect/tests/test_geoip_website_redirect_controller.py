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
from unittest.mock import patch, Mock
from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged('post_install', '-at_install')
class TestGeoipWebsiteRedirectController(HttpCase):

    def test_web_login_route(self):
        """Test web login route."""
        response = self.url_open(
            '/web/login'
        )
        self.assertEqual(
            response.status_code,
            200
        )

    @patch(
        'odoo.addons.geoip_website_redirect.controllers.'
        'geoip_website_redirect.requests.get'
    )
    def test_controller_location_response(self, mock_get):
        """Test controller location fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'country': 'India'
        }
        mock_get.return_value = mock_response
        response = self.url_open(
            '/web/login?user_ip=8.8.8.8'
        )
        self.assertEqual(
            response.status_code,
            200
        )

    @patch(
        'odoo.addons.geoip_website_redirect.controllers.'
        'geoip_website_redirect.requests.get'
    )
    def test_controller_exception_handling(self, mock_get):
        """Test controller exception handling."""
        mock_get.side_effect = Exception(
            'Geoip Connection Error'
        )
        response = self.url_open(
            '/web/login?user_ip=8.8.8.8'
        )
        self.assertEqual(
            response.status_code,
            200
        )
