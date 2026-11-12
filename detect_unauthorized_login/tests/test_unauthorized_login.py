# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import re

import odoo.tests
from odoo.tests.common import HttpCase

@odoo.tests.tagged('post_install', '-at_install')
class TestUnauthorizedLogin(HttpCase):

    def setUp(self):
        super(TestUnauthorizedLogin, self).setUp()
        # Create a dedicated test user to avoid issues with admin password
        self.login = 'test_user_unauth'
        self.password = 'test_password'
        self.test_user = self.env['res.users'].sudo().create({
            'name': 'Test User Unauth',
            'login': self.login,
            'password': self.password,
            'email': 'test_user_unauth@example.com',
            'group_ids': [(4, self.env.ref('base.group_user').id)]
        })

    def test_unauthorized_login_capture(self):
        """Test that an unauthorized login attempt creates an auto.capture record and sends a mail"""
        db_name = self.env.cr.dbname
        login = self.login
        password = 'wrong_password'

        # Count initial captures and mails
        initial_captures = self.env['auto.capture'].sudo().search_count([])
        initial_mails = self.env['mail.mail'].sudo().search_count([])

        # Perform a login attempt with wrong password
        # self.url_open handles the session and CSRF if we are careful
        # In Odoo 17+, we can just post and it might work if we have a session
        
        # Step 1: Get the login page to initialize the session and get CSRF token
        res_get = self.url_open('/web/login')
        self.assertEqual(res_get.status_code, 200)
        
        # Extract CSRF token from the response text
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', res_get.text)
        csrf_token = csrf_match.group(1) if csrf_match else ''

        # Step 2: Post the login attempt
        response = self.url_open(
            '/web/login',
            data={
                'login': login,
                'password': password,
                'csrf_token': csrf_token,
                'db': db_name,
            },
            timeout=30
        )

        # Check if we got an error message in the response
        self.assertIn('Wrong login/password', response.text)

        # Check if a new auto.capture record was created
        final_captures = self.env['auto.capture'].sudo().search_count([])
        self.assertEqual(final_captures, initial_captures + 1, "An auto.capture record should have been created")

        # Verify the content of the capture
        last_capture = self.env['auto.capture'].sudo().search([], order='id desc', limit=1)
        self.assertEqual(last_capture.email, self.test_user.email)
        
        # Check if a mail was sent (mail.mail should be created because force_send=True is used in controller)
        # Actually force_send=True sends it immediately, so we might check mail.mail or the message log
        final_mails = self.env['mail.mail'].sudo().search_count([])
        self.assertTrue(final_mails > initial_mails, "A notification mail should have been created")

    def test_successful_login_no_capture(self):
        """Test that a successful login does NOT create an auto.capture record"""
        user = self.env['res.users'].sudo().search([('login', '=', self.login)])
        self.assertTrue(user, "Test user should exist")
        
        initial_captures = self.env['auto.capture'].sudo().search_count([])
        
        # Authenticate successfully with the test user via HTTP POST
        res_get = self.url_open('/web/login')
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', res_get.text)
        csrf_token = csrf_match.group(1) if csrf_match else ''

        response = self.url_open(
            '/web/login',
            data={
                'login': self.login,
                'password': self.password,
                'csrf_token': csrf_token,
            },
            timeout=30
        )
        
        # Check that we are redirected or logged in (no "Wrong login/password" in text)
        self.assertNotIn('Wrong login/password', response.text)
        
        # Check that no capture was created
        final_captures = self.env['auto.capture'].sudo().search_count([])
        self.assertEqual(final_captures, initial_captures, "No auto.capture record should be created for successful login")
