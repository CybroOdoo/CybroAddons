# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

import base64
import io
import lxml.html

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestCustomizeSignup(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Enable uninvited signup
        cls.env['res.config.settings'].create({
            'auth_signup_uninvited': 'b2c',
        }).execute()

        # Create or get a country for testing
        cls.country = cls.env['res.country'].search([('code', '=', 'ZZ')], limit=1)
        if not cls.country:
            cls.country = cls.env['res.country'].create({
                'name': 'Test Country',
                'code': 'ZZ',
            })

    def _get_csrf_token(self, url='/web/signup'):
        """Retrieve a valid CSRF token by parsing the rendered signup page."""
        self.authenticate(None, None)
        response = self.url_open(url)
        tree = lxml.html.fromstring(response.content)
        token_inputs = tree.xpath('//input[@name="csrf_token"]')
        self.assertTrue(token_inputs, "CSRF token input not found on the page")
        return token_inputs[0].get('value')

    def test_signup_page_template_rendering(self):
        """Test that the GET /web/signup page renders all custom fields, container, and toggle buttons."""
        self.authenticate(None, None)
        response = self.url_open('/web/signup')
        self.assertEqual(response.status_code, 200)

        tree = lxml.html.fromstring(response.content)

        # Check multipart form-data attribute
        forms = tree.xpath('//form[contains(@class, "oe_signup_form")]')
        self.assertTrue(forms, "Signup form should exist")
        self.assertEqual(forms[0].get('enctype'), 'multipart/form-data')

        # Check customized extra inputs
        self.assertTrue(tree.xpath('//div[@id="data"]'), "Extra info container #data should exist")
        self.assertTrue(tree.xpath('//input[@id="phone"][@name="phone"]'), "Phone input should exist")
        self.assertTrue(tree.xpath('//input[@id="city"][@name="city"]'), "City input should exist")
        self.assertTrue(tree.xpath('//input[@id="job_position"][@name="job_position"]'), "Job position input should exist")
        self.assertTrue(tree.xpath('//input[@id="file"][@name="file"]'), "File input should exist")
        self.assertTrue(tree.xpath('//select[@id="country"][@name="country"]'), "Country select should exist")

        # Check customized toggle buttons
        info_btn = tree.xpath('//*[@id="info"]')
        self.assertTrue(info_btn, "Extra Information button #info should exist")
        self.assertIn("Extra Information", info_btn[0].text_content())

        hide_info_btn = tree.xpath('//*[@id="hide_info"]')
        self.assertTrue(hide_info_btn, "Hide Information button #hide_info should exist")
        self.assertIn("Hide Information", hide_info_btn[0].text_content())

    def test_web_auth_signup_extra_fields(self):
        """Test signup with extra fields: phone, job_position, city, country, and file"""
        csrf_token = self._get_csrf_token()

        signup_url = '/web/signup'
        login = 'test_signup_extra@example.com'
        name = 'Test User Extra'
        password = 'password123'

        # Prepare file data (a tiny transparent PNG)
        file_content = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==')
        file_io = io.BytesIO(file_content)

        payload = {
            'login': login,
            'name': name,
            'password': password,
            'confirm_password': password,
            'csrf_token': csrf_token,
            'phone': '1234567890',
            'job_position': 'Developer',
            'city': 'Test City',
            'country': self.country.id,
        }

        files = {
            'file': ('test.png', file_io, 'image/png')
        }

        # Perform signup
        # We use url_open with data and files which triggers multipart/form-data
        response = self.url_open(signup_url, data=payload, files=files)

        # Check if signup was successful (redirected to successful login or portal home)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('/web/login_successful' in response.url or '/my' in response.url,
                        "Should redirect to login successful or portal home")

        # Verify user and partner data
        user = self.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        self.assertTrue(user, "User should be created")

        partner = user.partner_id
        self.assertEqual(partner.phone, '1234567890', "Phone should be stored")
        self.assertEqual(partner.function, 'Developer', "Job position should be stored in function field")
        self.assertEqual(partner.city, 'Test City', "City should be stored")
        self.assertEqual(partner.country_id.id, self.country.id, "Country should be stored")

        # Verify image was stored
        self.assertTrue(partner.image_1920, "Image should be stored")

    def test_web_auth_signup_partial_info(self):
        """Test signup with only some extra fields"""
        csrf_token = self._get_csrf_token()

        login = 'test_signup_partial@example.com'
        payload = {
            'login': login,
            'name': 'Partial User',
            'password': 'password123',
            'confirm_password': 'password123',
            'csrf_token': csrf_token,
            'phone': '9999999999',
            # city, job_position, country, file omitted
        }

        self.url_open('/web/signup', data=payload)

        user = self.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        self.assertTrue(user)
        self.assertEqual(user.partner_id.phone, '9999999999')
        self.assertFalse(user.partner_id.city)

    def test_web_auth_signup_without_extra_fields(self):
        """Test signup when standard form is submitted with no extra fields at all."""
        csrf_token = self._get_csrf_token()

        login = 'test_signup_no_extra@example.com'
        payload = {
            'login': login,
            'name': 'No Extra User',
            'password': 'password123',
            'confirm_password': 'password123',
            'csrf_token': csrf_token,
        }

        response = self.url_open('/web/signup', data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('/web/login_successful' in response.url or '/my' in response.url)

        user = self.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        self.assertTrue(user)
        self.assertFalse(user.partner_id.phone)
        self.assertFalse(user.partner_id.city)
        self.assertFalse(user.partner_id.function)
        self.assertFalse(user.partner_id.image_1920)

    def test_web_auth_signup_with_invalid_country(self):
        """Test signup with an invalid/non-existent country ID gracefully handles it."""
        csrf_token = self._get_csrf_token()

        login = 'test_signup_invalid_country@example.com'
        payload = {
            'login': login,
            'name': 'Invalid Country User',
            'password': 'password123',
            'confirm_password': 'password123',
            'csrf_token': csrf_token,
            'country': 99999999,
            'phone': '1231231234',
        }

        response = self.url_open('/web/signup', data=payload)
        self.assertEqual(response.status_code, 200)

        user = self.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        self.assertTrue(user)
        self.assertEqual(user.partner_id.phone, '1231231234')
        self.assertFalse(user.partner_id.country_id, "Non-existent country ID should not set country_id")

    def test_web_auth_signup_empty_file_upload(self):
        """Test that submitting an empty file object does not corrupt or set image_1920."""
        csrf_token = self._get_csrf_token()

        login = 'test_signup_empty_file@example.com'
        payload = {
            'login': login,
            'name': 'Empty File User',
            'password': 'password123',
            'confirm_password': 'password123',
            'csrf_token': csrf_token,
            'city': 'Empty File City',
        }
        empty_file = io.BytesIO(b'')
        files = {
            'file': ('', empty_file, 'application/octet-stream')
        }

        response = self.url_open('/web/signup', data=payload, files=files)
        self.assertEqual(response.status_code, 200)

        user = self.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        self.assertTrue(user)
        self.assertEqual(user.partner_id.city, 'Empty File City')
        self.assertFalse(user.partner_id.image_1920)

    def test_web_auth_signup_failed_does_not_overwrite_partner(self):
        """Test that failed signup attempts do not overwrite existing partner details."""
        existing_login = 'guarded_existing_partner@example.com'
        original_image = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==')
        existing_user = self.env['res.users'].create({
            'name': 'Guarded Existing Partner',
            'login': existing_login,
            'email': existing_login,
            'password': 'initial_password123',
            'phone': '1111111111',
            'function': 'Architect',
            'city': 'Original City',
            'country_id': self.country.id,
            'image_1920': base64.b64encode(original_image),
        })
        existing_partner = existing_user.partner_id

        csrf_token = self._get_csrf_token()

        # 1. Attempt signup with existing login (fails due to duplicate email/login)
        new_image_file = io.BytesIO(b'malicious_payload_or_new_image')
        payload = {
            'login': existing_login,
            'name': 'Should Not Overwrite',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'csrf_token': csrf_token,
            'phone': '9999999999',
            'job_position': 'Hacker',
            'city': 'Overwritten City',
            'country': self.country.id,
        }
        files = {
            'file': ('attack.png', new_image_file, 'image/png')
        }

        response = self.url_open('/web/signup', data=payload, files=files)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('/web/signup' in response.url, "Should stay on signup page upon failure")
        self.assertIn("Another user is already registered", response.text)

        # Verify existing partner data remains untouched
        existing_partner.invalidate_recordset()
        self.assertEqual(existing_partner.phone, '1111111111', "Phone should NOT be overwritten on failed signup")
        self.assertEqual(existing_partner.function, 'Architect', "Function should NOT be overwritten on failed signup")
        self.assertEqual(existing_partner.city, 'Original City', "City should NOT be overwritten on failed signup")
        self.assertEqual(existing_partner.country_id.id, self.country.id, "Country should NOT be overwritten on failed signup")
        self.assertEqual(base64.b64decode(existing_partner.image_1920), original_image, "Image should NOT be overwritten on failed signup")

        # 2. Attempt signup with password mismatch (fails password confirmation)
        csrf_token = self._get_csrf_token()
        mismatch_payload = {
            'login': existing_login,
            'name': 'Mismatch Test',
            'password': 'passwordAAA',
            'confirm_password': 'passwordBBB',
            'csrf_token': csrf_token,
            'phone': '8888888888',
        }
        response = self.url_open('/web/signup', data=mismatch_payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('/web/signup' in response.url)

        existing_partner.invalidate_recordset()
        self.assertEqual(existing_partner.phone, '1111111111', "Phone should still NOT be overwritten on password mismatch")

    def test_web_auth_signup_non_image_file_rejected(self):
        """Test that uploading a non-image file (e.g. text or arbitrary data) does not set image_1920."""
        csrf_token = self._get_csrf_token()

        login = 'test_signup_non_image@example.com'
        payload = {
            'login': login,
            'name': 'Non Image User',
            'password': 'password123',
            'confirm_password': 'password123',
            'csrf_token': csrf_token,
            'phone': '5555555555',
        }
        non_image_file = io.BytesIO(b'This is a plain text file, definitely not an image!')
        files = {
            'file': ('test.txt', non_image_file, 'text/plain')
        }

        response = self.url_open('/web/signup', data=payload, files=files)
        self.assertEqual(response.status_code, 200)

        user = self.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        self.assertTrue(user)
        self.assertEqual(user.partner_id.phone, '5555555555')
        self.assertFalse(user.partner_id.image_1920, "Non-image file must not be stored in image_1920")
