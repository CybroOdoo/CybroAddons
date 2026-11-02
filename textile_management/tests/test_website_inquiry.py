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
import re

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWebsiteInquiry(HttpCase):
    """Test the textile inquiry form and the inquiry records."""

    def test_01_inquiry_name_and_states(self):
        """The inquiry is named after the inquirer and moves through its
        states."""
        inquiry = self.env['website.inquiry'].create({
            'inquirer': 'Jane Doe', 'email': 'jane@example.com',
            'created_date': '2026-10-01',
        })
        self.assertEqual(inquiry.name, 'Jane Doe / 2026-10-01')
        self.assertEqual(inquiry.state, 'draft')
        inquiry.action_verified()
        self.assertEqual(inquiry.state, 'verified')
        inquiry.action_replied()
        self.assertEqual(inquiry.state, 'replied')

    def _get_csrf_token(self):
        """Open the form and return its CSRF token."""
        response = self.url_open('/textile/inquiry/form')
        self.assertEqual(response.status_code, 200)
        return re.search(r'name="csrf_token" value="([^"]+)"',
                         response.text).group(1)

    def test_02_submit_inquiry(self):
        """Submitting the form creates the inquiry and shows the thank-you
        page with the company contacts."""
        self.env.ref('base.default_website').company_id.write({
            'email': 'textile@example.com', 'phone': '+1 555 0100'})
        response = self.url_open('/textile/inquiry/form/submit', data={
            'csrf_token': self._get_csrf_token(),
            'name': ' Jane Doe ', 'email': 'jane@example.com',
            'number': '555 0199', 'description': 'Need <b>cotton</b>\nfast',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.url.endswith('/textile/inquiry/thank-you'))
        self.assertIn('textile@example.com', response.text)
        inquiry = self.env['website.inquiry'].search(
            [('email', '=', 'jane@example.com')])
        self.assertEqual(inquiry.inquirer, 'Jane Doe')
        self.assertEqual(inquiry.phone_number, '555 0199')
        # The description is escaped, not interpreted as HTML
        self.assertNotIn('<b>', inquiry.description)
        self.assertIn('&lt;b&gt;cotton', inquiry.description)

    def test_03_submit_without_csrf_token(self):
        """The form is protected against cross-site request forgery."""
        response = self.url_open('/textile/inquiry/form/submit', data={
            'name': 'Spammer', 'email': 'spam@example.com'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.env['website.inquiry'].search(
            [('email', '=', 'spam@example.com')]))

    def test_04_submit_without_required_fields(self):
        """A submission without name or email goes back to the form."""
        response = self.url_open('/textile/inquiry/form/submit', data={
            'csrf_token': self._get_csrf_token(), 'name': ' ', 'email': ''},
            allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers['Location'].endswith(
            '/textile/inquiry/form'))

    def test_05_submit_with_invalid_email(self):
        """An email address that cannot be replied to goes back to the form."""
        response = self.url_open('/textile/inquiry/form/submit', data={
            'csrf_token': self._get_csrf_token(), 'name': 'Jane Doe',
            'email': 'not-an-email'}, allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertFalse(self.env['website.inquiry'].search(
            [('email', '=', 'not-an-email')]))
