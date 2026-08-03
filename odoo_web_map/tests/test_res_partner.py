# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from unittest.mock import patch, MagicMock

class TestResPartner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestResPartner, cls).setUpClass()
        cls.country = cls.env['res.country'].search([], limit=1)
        if not cls.country:
            cls.country = cls.env['res.country'].create({'name': 'Test Country', 'code': 'XZTest'})
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'street': 'Main St',
            'city': 'Metropolis',
            'country_id': cls.country.id
        })
        
    @patch('odoo.addons.odoo_web_map.models.res_partner.requests.get')
    def test_action_geo_localize_nominatim_success(self, mock_get):
        """Test simulating geolocating a partner from coordinates"""
        mock_response = MagicMock()
        # Mock high importance object match
        mock_response.json.return_value = [{'lat': '50.0', 'lon': '10.0', 'importance': '0.5'}]
        mock_get.return_value = mock_response

        # the localization sets coordinates
        self.partner.action_geo_localize_nominatim()
        
        self.assertEqual(self.partner.partner_latitude, 50.0)
        self.assertEqual(self.partner.partner_longitude, 10.0)

    @patch('odoo.addons.odoo_web_map.models.res_partner.requests.get')
    def test_action_geo_localize_nominatim_failure(self, mock_get):
        """Test failure scenario raises descriptive errors from unmapped results"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        with self.assertRaises(UserError):
            self.partner.action_geo_localize_nominatim()
