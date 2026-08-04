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
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
import json

class TestResPartner(TransactionCase):

    def setUp(self):
        super().setUp()
        self.country = self.env['res.country'].create({
            'name': 'Test Country',
            'code': 'ZZ',
        })
        self.state = self.env['res.country.state'].create({
            'name': 'Test State',
            'code': 'TS',
            'country_id': self.country.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'street': '123 Fake St',
            'city': 'Fakeville',
            'state_id': self.state.id,
            'zip': '12345',
            'country_id': self.country.id,
        })

    def test_01_get_geocoding_strategies(self):
        """ Test multiple queries generation strategies """
        strategies = self.partner._get_geocoding_strategies(self.partner)
        names = [s[0] for s in strategies]
        self.assertListEqual(names, ['structured', 'full_address', 'city_country', 'country_only'])
        
        # Verify structured params
        structured_params = strategies[0][1]
        self.assertEqual(structured_params['street'], '123 Fake St')
        self.assertEqual(structured_params['city'], 'Fakeville')
        self.assertEqual(structured_params['country'], 'ZZ')

        # Test partial partner strategies
        partial_partner = self.env['res.partner'].create({
            'name': 'Partial',
            'country_id': self.country.id,
        })
        strategies_partial = partial_partner._get_geocoding_strategies(partial_partner)
        names_partial = [s[0] for s in strategies_partial]
        self.assertListEqual(names_partial, ['full_address', 'country_only'])
        
    @patch('odoo.addons.odoo_web_map.models.res_partner.requests.get')
    def test_02_action_geo_localize_success(self, mock_get):
        """ Test successful geolocalization """
        class MockResponse:
            def __init__(self, data, status_code=200):
                self._data = data
                self.status_code = status_code
            def json(self):
                return self._data
            def raise_for_status(self):
                pass

        # Mocking the response with dummy coordinates
        mock_get.return_value = MockResponse([
            {'lat': '40.7128', 'lon': '-74.0060', 'importance': 0.6}
        ])

        self.partner.action_geo_localize_nominatim()
        self.assertEqual(self.partner.partner_latitude, 40.7128)
        self.assertEqual(self.partner.partner_longitude, -74.0060)
        self.assertTrue(self.partner.date_localization)
        self.assertEqual(mock_get.call_count, 1)

    @patch('odoo.addons.odoo_web_map.models.res_partner.requests.get')
    def test_03_action_geo_localize_failure(self, mock_get):
        """ Test geolocalization fails when API returns no results """
        class MockResponse:
            def __init__(self, data, status_code=200):
                self._data = data
                self.status_code = status_code
            def json(self):
                return self._data
            def raise_for_status(self):
                pass
        
        # Mocking empty response
        mock_get.return_value = MockResponse([])

        with self.assertRaises(UserError):
            self.partner.action_geo_localize_nominatim()
        
        # It tries all 4 strategies empty resulting in failure
        self.assertEqual(mock_get.call_count, 4)
