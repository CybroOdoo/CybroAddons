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
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestResPartner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Find any available country in the database to use
        cls.country = cls.env['res.country'].search([], limit=1)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'street': '1600 Amphitheatre Pkwy',
            'city': 'Mountain View',
            'zip': '94043',
            'country_id': cls.country.id if cls.country else False,
        })

    def test_01_get_geocoding_strategies(self):
        """Test _get_geocoding_strategies returns expected fallback list."""
        strategies = self.partner._get_geocoding_strategies(self.partner)
        self.assertTrue(len(strategies) > 0, "At least one strategy should be generated")
        
        # Check first strategy structure
        strategy_name, params = strategies[0]
        self.assertEqual(strategy_name, 'structured')
        self.assertEqual(params.get('city'), 'Mountain View')
        self.assertEqual(params.get('postalcode'), '94043')

    def test_02_action_geo_localize_nominatim_success(self):
        """Test action_geo_localize_nominatim with a successful API response."""
        mock_response = [{
            'lat': '37.4220',
            'lon': '-122.0841',
            'importance': 0.8,
        }]
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.status_code = 200
            
            self.partner.action_geo_localize_nominatim()
            
            self.assertAlmostEqual(self.partner.partner_latitude, 37.4220)
            self.assertAlmostEqual(self.partner.partner_longitude, -122.0841)
            self.assertTrue(self.partner.date_localization)

    def test_03_action_geo_localize_nominatim_failure(self):
        """Test action_geo_localize_nominatim handles failure by raising UserError."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = []
            mock_get.return_value.status_code = 200
            
            with self.assertRaises(UserError):
                self.partner.action_geo_localize_nominatim()
