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
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestGeoipWebsiteRedirect(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].get_current_website()
        cls.user = cls.env['res.users'].create({
            'name': 'Geo User',
            'login': 'geo_user',
            'email': 'geo@test.com',
            'password': 'admin',
            'ip_address': '8.8.8.8',
        })

    @patch(
        'odoo.addons.geoip_website_redirect.models.website.requests.get'
    )
    def test_get_user_location(self, mock_get):
        """Test fetching user location."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'country': 'India'
        }
        mock_get.return_value = mock_response
        result = self.website.with_user(
            self.user
        ).get_user_location()
        self.assertEqual(
            result['country'],
            'India'
        )

    @patch(
        'odoo.addons.geoip_website_redirect.models.website.requests.get'
    )
    def test_invalid_geoip_response(self, mock_get):
        """Test invalid geoip response."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        result = self.website.with_user(
            self.user
        ).get_user_location()
        self.assertEqual(
            result,
            {'country': None}
        )

    @patch(
        'odoo.addons.geoip_website_redirect.models.website.requests.get'
    )
    def test_pricelist_update(self, mock_get):
        """Test pricelist update based on country."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'country': 'India'
        }
        mock_get.return_value = mock_response
        pricelist = self.website.with_user(
            self.user
        )._get_and_cache_current_pricelist()
        self.assertTrue(
            pricelist
        )
        self.assertTrue(
            pricelist.currency_id
        )
