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
from unittest.mock import MagicMock, patch

import requests
from odoo.addons.website_sale.tests.common import MockRequest
from odoo.tests.common import TransactionCase, tagged

from .. import _post_init_hook
from ..controllers.geoip_website_redirect import Geolocation


@tagged('post_install', '-at_install')
class TestResUsersIpAddress(TransactionCase):
    """Test suite for ip_address field on res.users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user_1 = cls.env['res.users'].create({
            'name': 'GeoIP Test User 1',
            'login': 'geoip_test_user_1@example.com',
            'ip_address': '192.168.1.10',
        })
        cls.test_user_2 = cls.env['res.users'].create({
            'name': 'GeoIP Test User 2',
            'login': 'geoip_test_user_2@example.com',
            'ip_address': '192.168.1.20',
        })

    def test_01_user_ip_address_crud(self):
        """Test read and write on user ip_address field."""
        self.assertEqual(self.test_user_1.ip_address, '192.168.1.10')
        self.test_user_1.write({'ip_address': '10.0.0.1'})
        self.assertEqual(self.test_user_1.ip_address, '10.0.0.1')

    def test_02_user_ip_address_multi_recordset(self):
        """Test multi-recordset operations on res.users ip_address."""
        users = self.test_user_1 + self.test_user_2
        users.write({'ip_address': '172.16.0.50'})
        for user in users:
            self.assertEqual(user.ip_address, '172.16.0.50')


@tagged('post_install', '-at_install')
class TestWebsiteGeoip(TransactionCase):
    """Test suite for GeoIP-based website methods and pricelist resolution."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        if not cls.website:
            cls.website = cls.env['website'].create({
                'name': 'Test Website GeoIP',
            })

        cls.public_user = cls.env.ref('base.public_user', raise_if_not_found=False)
        if not cls.public_user:
            cls.public_user = cls.env['res.users'].create({
                'name': 'Test Public User',
                'login': 'test_public_user@example.com',
            })

        cls.currency_usd = cls.env.ref('base.USD', raise_if_not_found=False) or cls.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not cls.currency_usd:
            cls.currency_usd = cls.env['res.currency'].create({
                'name': 'USD',
                'symbol': '$',
            })
        cls.currency_usd.write({'active': True})

        cls.currency_inr = cls.env.ref('base.INR', raise_if_not_found=False) or cls.env['res.currency'].search([('name', '=', 'INR')], limit=1)
        if not cls.currency_inr:
            cls.currency_inr = cls.env['res.currency'].create({
                'name': 'INR',
                'symbol': '₹',
            })
        cls.currency_inr.write({'active': True})

        cls.pricelist_usd = cls.env['product.pricelist'].create({
            'name': 'USD Test Pricelist',
            'currency_id': cls.currency_usd.id,
            'website_id': cls.website.id,
        })
        cls.pricelist_inr = cls.env['product.pricelist'].create({
            'name': 'INR Test Pricelist',
            'currency_id': cls.currency_inr.id,
            'website_id': cls.website.id,
        })

    def test_01_get_user_location_from_session(self):
        """Test location retrieval when IP is present in session."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'country': 'United States'}

        with MockRequest(self.env, website=self.website) as req:
            req.session['user_ip'] = '8.8.8.8'
            with patch('requests.get', return_value=mock_response):
                country = self.website.get_user_location()
                self.assertEqual(country, 'United States')

    def test_02_get_user_location_from_user_field(self):
        """Test location retrieval falling back to user's ip_address field."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'country': 'India'}

        user = self.env['res.users'].create({
            'name': 'GeoIP Location User',
            'login': 'geoip_loc_user@example.com',
            'ip_address': '103.21.244.0',
        })
        website_user_env = self.website.with_user(user)

        with MockRequest(self.env(user=user), website=self.website) as req:
            req.session.pop('user_ip', None)
            with patch('requests.get', return_value=mock_response):
                country = website_user_env.get_user_location()
                self.assertEqual(country, 'India')

    def test_03_get_user_location_no_ip(self):
        """Test location retrieval when no IP is found."""
        user = self.env['res.users'].create({
            'name': 'No IP User',
            'login': 'no_ip_user@example.com',
            'ip_address': False,
        })
        website_user_env = self.website.with_user(user)

        with MockRequest(self.env(user=user), website=self.website) as req:
            req.session.pop('user_ip', None)
            country = website_user_env.get_user_location()
            self.assertIsNone(country)

    def test_04_get_user_location_network_error(self):
        """Test location retrieval when HTTP request fails."""
        with MockRequest(self.env, website=self.website) as req:
            req.session['user_ip'] = '8.8.8.8'
            with patch('requests.get', side_effect=requests.RequestException("Lookup error")):
                country = self.website.get_user_location()
                self.assertIsNone(country)

    def test_05_pricelist_for_country_valid(self):
        """Test pricelist resolution for a known valid country."""
        pricelist = self.website._pricelist_for_country('United States')
        self.assertIsNotNone(pricelist)
        self.assertEqual(pricelist.currency_id.name, 'USD')

    def test_06_pricelist_for_country_invalid_or_unknown(self):
        """Test pricelist resolution for an unknown country."""
        pricelist = self.website._pricelist_for_country('AtlantisNonExistent')
        self.assertIsNone(pricelist)

    def test_07_pricelist_for_country_no_matching_currency(self):
        """Test pricelist resolution when country has no matching currencies."""
        with patch('countryinfo.CountryInfo.currencies', return_value=[]), \
             patch.object(type(self.env['res.country']), 'search', return_value=self.env['res.country']):
            pricelist = self.website._pricelist_for_country('United States')
            self.assertIsNone(pricelist)

    def test_08_pricelist_for_country_currency_not_in_system(self):
        """Test pricelist resolution when currency does not exist in res.currency."""
        with patch('countryinfo.CountryInfo.currencies', return_value=['NONEXISTENT_CURR']), \
             patch.object(type(self.env['res.country']), 'search', return_value=self.env['res.country']):
            pricelist = self.website._pricelist_for_country('United States')
            self.assertIsNone(pricelist)

    def test_08b_pricelist_for_country_inactive_currency(self):
        """Test pricelist resolution returns None without DB writes when currency is inactive."""
        curr_jpy = self.env.ref('base.JPY', raise_if_not_found=False) or self.env['res.currency'].search([('name', '=', 'JPY')], limit=1)
        if not curr_jpy:
            curr_jpy = self.env['res.currency'].create({'name': 'JPY', 'symbol': '¥'})
        curr_jpy.write({'active': False})
        pricelist = self.website._pricelist_for_country('Japan')
        self.assertIsNone(pricelist)
        self.assertFalse(curr_jpy.active)

    def test_09_pricelist_for_country_fallback_search(self):
        """Test fallback to any product.pricelist when not in website available pricelists."""
        curr_eur = self.env.ref('base.EUR', raise_if_not_found=False) or self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
        if not curr_eur:
            curr_eur = self.env['res.currency'].create({'name': 'EUR', 'symbol': '€'})
        curr_eur.write({'active': True})

        self.env['product.pricelist'].create({
            'name': 'EUR System Fallback Pricelist',
            'currency_id': curr_eur.id,
            'website_id': False,
        })
        with patch.object(type(self.website), 'get_pricelist_available', return_value=self.env['product.pricelist']):
            pricelist = self.website._pricelist_for_country('France')
            self.assertIsNotNone(pricelist)
            self.assertEqual(pricelist.currency_id, curr_eur)

    def test_10_get_and_cache_current_pricelist_logged_in_user(self):
        """Test pricelist caching for authenticated (non-public) user."""
        admin_user = self.env.ref('base.user_admin')
        website_admin_env = self.website.with_user(admin_user)

        with MockRequest(self.env(user=admin_user), website=self.website):
            with patch.object(type(self.website), 'get_user_location') as mock_geo:
                pl = website_admin_env._get_and_cache_current_pricelist()
                mock_geo.assert_not_called()
                self.assertTrue(pl)

    def test_11_get_and_cache_current_pricelist_public_with_session(self):
        """Test public user when pricelist is already cached in session."""
        website_public_env = self.website.with_user(self.public_user)

        with MockRequest(self.env(user=self.public_user), website=self.website) as req:
            req.session['website_sale_current_pl'] = self.pricelist_usd.id
            with patch.object(type(self.website), '_pricelist_for_country') as mock_country:
                pl = website_public_env._get_and_cache_current_pricelist()
                mock_country.assert_not_called()
                self.assertEqual(pl.id, self.pricelist_usd.id)

    def test_12_get_and_cache_current_pricelist_public_geoip_detect(self):
        """Test public user first visit GeoIP pricelist auto-detection with session IP."""
        website_public_env = self.website.with_user(self.public_user)
        mock_geo_resp = MagicMock()
        mock_geo_resp.json.return_value = {'country': 'United States'}

        with MockRequest(self.env(user=self.public_user), website=self.website) as req:
            req.session.pop('website_sale_current_pl', None)
            req.session['user_ip'] = '8.8.8.8'

            with patch('requests.get', return_value=mock_geo_resp):
                pl = website_public_env._get_and_cache_current_pricelist()
                self.assertEqual(req.session.get('website_sale_current_pl'), pl.id)
                self.assertEqual(pl.currency_id.name, 'USD')

    def test_13_get_and_cache_current_pricelist_public_ipify_lookup(self):
        """Test public user with no session IP triggers ipify then ip-api lookup."""
        website_public_env = self.website.with_user(self.public_user)

        def mock_requests_get(url, **_kwargs):
            resp = MagicMock()
            if 'ipify.org' in url:
                resp.status_code = 200
                resp.json.return_value = {'ip': '8.8.8.8'}
            elif 'ip-api.com' in url:
                resp.status_code = 200
                resp.json.return_value = {'country': 'India'}
            else:
                resp.status_code = 404
                resp.json.return_value = {}
            return resp

        with MockRequest(self.env(user=self.public_user), website=self.website) as req:
            req.session.pop('website_sale_current_pl', None)
            req.session.pop('user_ip', None)

            with patch('requests.get', side_effect=mock_requests_get):
                pl = website_public_env._get_and_cache_current_pricelist()
                self.assertEqual(req.session.get('user_ip'), '8.8.8.8')
                self.assertEqual(req.session.get('website_sale_current_pl'), pl.id)
                self.assertEqual(pl.currency_id.name, 'INR')

    def test_14_get_and_cache_current_pricelist_public_network_error(self):
        """Test graceful fallback when network lookup raises an exception."""
        website_public_env = self.website.with_user(self.public_user)

        with MockRequest(self.env(user=self.public_user), website=self.website) as req:
            req.session.pop('website_sale_current_pl', None)
            req.session['user_ip'] = '8.8.8.8'

            with patch('requests.get', side_effect=Exception("GeoIP server offline")):
                pl = website_public_env._get_and_cache_current_pricelist()
                self.assertTrue(pl)

    def test_15_website_multi_recordset(self):
        """Test multi-recordset website execution."""
        second_website = self.env['website'].create({
            'name': 'Second Test Website',
        })
        websites = self.website + second_website
        names = websites.mapped('name')
        self.assertIn(self.website.name, names)
        self.assertIn('Second Test Website', names)

    def test_16_post_init_hook_execution(self):
        """Test that _post_init_hook runs cleanly and creates pricelists."""
        _post_init_hook(self.env)
        inr_curr = self.env['res.currency'].search([('name', '=', 'INR')], limit=1)
        if inr_curr:
            self.assertTrue(inr_curr.active)
            pl = self.env['product.pricelist'].search([('currency_id', '=', inr_curr.id)], limit=1)
            self.assertTrue(pl)


@tagged('post_install', '-at_install')
class TestGeoipController(TransactionCase):
    """Test suite for Geolocation controller routes and helper functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        if not cls.website:
            cls.website = cls.env['website'].create({
                'name': 'Controller Test Website',
            })

        cls.test_user = cls.env['res.users'].create({
            'name': 'Controller Test User',
            'login': 'controller_test_user@example.com',
            'ip_address': '8.8.8.8',
        })

        cls.currency_usd = cls.env.ref('base.USD', raise_if_not_found=False) or cls.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not cls.currency_usd:
            cls.currency_usd = cls.env['res.currency'].create({'name': 'USD', 'symbol': '$'})
        cls.currency_usd.write({'active': True})

        cls.pricelist_usd = cls.env['product.pricelist'].create({
            'name': 'Controller USD Pricelist',
            'currency_id': cls.currency_usd.id,
            'website_id': cls.website.id,
        })

    def test_01_get_ip_location_helper(self):
        """Test _get_ip_location with valid, empty, and failing calls."""
        controller = Geolocation()
        self.assertEqual(controller._get_ip_location(''), {})

        mock_resp = MagicMock()
        mock_resp.json.return_value = {'country': 'United States'}
        with patch('requests.get', return_value=mock_resp):
            res = controller._get_ip_location('8.8.8.8')
            self.assertEqual(res, {'country': 'United States'})

        with patch('requests.get', side_effect=Exception("Network error")):
            res = controller._get_ip_location('8.8.8.8')
            self.assertEqual(res, {})

    def test_02_apply_lang_and_currency_helper(self):
        """Test _apply_lang_and_currency with valid and invalid countries."""
        controller = Geolocation()
        with MockRequest(self.env, website=self.website):
            lang, pricelist = controller._apply_lang_and_currency('United States', user=self.test_user)
            self.assertIsNotNone(pricelist)

            lang_invalid, pricelist_invalid = controller._apply_lang_and_currency('UnknownCountryFake', user=self.test_user)
            self.assertIsNone(lang_invalid)
            self.assertIsNone(pricelist_invalid)

    def test_02b_apply_lang_and_currency_dynamic_inactive_currency(self):
        """Test _apply_lang_and_currency dynamically activates inactive currency and creates pricelist."""
        curr_jpy = self.env.ref('base.JPY', raise_if_not_found=False) or self.env['res.currency'].search([('name', '=', 'JPY')], limit=1)
        if not curr_jpy:
            curr_jpy = self.env['res.currency'].create({'name': 'JPY', 'symbol': '¥'})
        curr_jpy.write({'active': False})

        self.env['product.pricelist'].search([('currency_id', '=', curr_jpy.id)]).unlink()

        controller = Geolocation()
        with MockRequest(self.env, website=self.website) as req:
            _lang, pricelist = controller._apply_lang_and_currency('Japan', user=self.test_user)
            self.assertTrue(curr_jpy.active)
            self.assertIsNotNone(pricelist)
            self.assertEqual(pricelist.currency_id, curr_jpy)
            self.assertEqual(req.session.get('website_sale_current_pl'), pricelist.id)
            self.assertEqual(self.test_user.partner_id.property_product_pricelist, pricelist)

    def test_03_web_login_override_unauthenticated(self):
        """Test web_login when user is not authenticated."""
        controller = Geolocation()
        with MockRequest(self.env, website=self.website) as req:
            req.session.uid = False
            with patch('odoo.addons.web.controllers.home.Home.web_login', return_value='login_page'):
                res = controller.web_login.original_endpoint(controller)
                self.assertEqual(res, 'login_page')

    def test_04_web_login_override_authenticated(self):
        """Test web_login applies GeoIP settings on successful user authentication."""
        controller = Geolocation()
        with MockRequest(self.env, website=self.website) as req:
            req.session.uid = self.test_user.id
            req.env = self.env(user=self.test_user)

            with patch('odoo.addons.web.controllers.home.Home.web_login', return_value='logged_in_redirect'), \
                 patch.object(Geolocation, '_get_ip_location', return_value={'country': 'United States'}), \
                 patch.object(Geolocation, '_apply_lang_and_currency', return_value=(None, self.pricelist_usd)):
                res = controller.web_login.original_endpoint(controller, user_ip='8.8.8.8')
                self.assertEqual(res, 'logged_in_redirect')
                self.assertEqual(self.test_user.ip_address, '8.8.8.8')

    def test_05_set_currency_by_lang_no_param(self):
        """Test set_currency_by_lang without lang_url_code returns error."""
        controller = Geolocation()
        with MockRequest(self.env, website=self.website):
            res = controller.set_currency_by_lang()
            self.assertFalse(res.get('success'))
            self.assertEqual(res.get('error'), 'No lang_url_code provided')

    def test_06_set_currency_by_lang_unknown_lang(self):
        """Test set_currency_by_lang with unknown language code returns error."""
        controller = Geolocation()
        with MockRequest(self.env, website=self.website):
            res = controller.set_currency_by_lang(lang_url_code='non_existent_code_xyz')
            self.assertFalse(res.get('success'))
            self.assertIn('Language not found', res.get('error'))

    def test_07_set_currency_by_lang_valid_lang(self):
        """Test set_currency_by_lang with valid language resolves pricelist."""
        controller = Geolocation()
        lang_en = self.env['res.lang'].search([('code', '=', 'en_US')], limit=1)
        if not lang_en:
            lang_en = self.env['res.lang'].create({
                'name': 'English',
                'code': 'en_US',
                'iso_code': 'en',
                'url_code': 'en',
            })

        with MockRequest(self.env, website=self.website):
            with patch.object(Geolocation, '_apply_lang_and_currency', return_value=(lang_en, self.pricelist_usd)):
                res = controller.set_currency_by_lang(lang_url_code=lang_en.url_code)
                self.assertTrue(res.get('success'))
                self.assertEqual(res.get('pricelist_id'), self.pricelist_usd.id)

    def test_08_set_currency_by_lang_exception_handling(self):
        """Test set_currency_by_lang handles exceptions without crashing."""
        controller = Geolocation()
        with MockRequest(self.env, website=self.website):
            with patch.object(Geolocation, '_apply_lang_and_currency', side_effect=Exception("Database error")):
                res = controller.set_currency_by_lang(lang_url_code='en')
                self.assertFalse(res.get('success'))
                self.assertIn('Database error', res.get('error'))