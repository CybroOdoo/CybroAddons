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
from datetime import date
from urllib.parse import urlsplit

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestAgeVerification(HttpCase):
    """Test the age verification of the website signup page."""

    def setUp(self):
        super().setUp()
        self.env['website'].search([]).auth_signup_uninvited = 'b2c'

    def test_signup_page_has_the_popup(self):
        """The signup page shows the popup with no future birth date"""
        response = self.url_open('/web/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_age_verify_date', response.text)
        self.assertIn(f'max="{date.today()}"', response.text)

    def test_login_page_has_no_popup(self):
        """The login page has no popup"""
        response = self.url_open('/web/login')
        self.assertNotIn('o_age_verify_date', response.text)

    def test_age_verification_tour(self):
        """A child is refused and an adult unlocks the signup form"""
        self.start_tour('/web/signup', 'age_verification_tour')

    def test_invitation_link_skips_popup(self):
        """An invited user opens the signup form without the popup"""
        partner = self.env['res.partner'].create(
            {'name': 'Invited Customer', 'email': 'invited@example.com'})
        partner.signup_prepare()
        url = urlsplit(partner._get_signup_url_for_action()[partner.id])
        path = f'{url.path}?{url.query}'
        self.assertTrue(url.path.endswith('/web/signup'))
        response = self.url_open(path)
        self.assertIn('value="invited@example.com"', response.text)
        self.start_tour(path, 'age_verification_invite_tour')
