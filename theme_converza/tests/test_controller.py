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

from unittest.mock import patch

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestConverzaAuditController(HttpCase):
    """POST /converza/audit stores the lead as an outgoing mail."""

    SUBJECT = 'New Strategy Audit Request'

    def _post(self, data):
        MailMail = self.env.registry['mail.mail']
        with patch.object(MailMail, 'send', return_value=True) as send:
            response = self.url_open(
                '/converza/audit', data=data, allow_redirects=False)
        return response, send

    def _last_mail(self):
        return self.env['mail.mail'].sudo().search(
            [('subject', '=', self.SUBJECT)], order='id desc', limit=1)

    def test_submit_creates_mail_and_redirects(self):
        response, send = self._post({
            'First Name': 'Jane',
            'Last Name': 'Smith',
            'Email': 'jane@example.com',
            'Company': 'Acme Inc.',
            'Website': 'https://acme.example',
            'Service Interest': 'SEO',
            'Budget': '5000',
            'Goals': 'More leads',
        })
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers['Location'].endswith(
            '/contactus-thank-you'))
        send.assert_called_once()

        mail = self._last_mail()
        self.assertTrue(mail)
        self.assertEqual(mail.email_to, 'hello@converza.agency')
        self.assertEqual(mail.email_from, 'jane@example.com')
        for expected in ('Jane', 'Smith', 'Acme Inc.', 'SEO', 'More leads'):
            self.assertIn(expected, mail.body_html)

    def test_missing_fields_do_not_crash(self):
        # url_open sends a GET for an empty dict, so post one field.
        response, _send = self._post({'Goals': 'Only goals given'})
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertEqual(self._last_mail().email_from, 'noreply@converza.agency')

    def test_html_in_input_is_escaped(self):
        self._post({'Goals': '<script>alert(1)</script>'})
        body = self._last_mail().body_html
        self.assertNotIn('<script>', body)
        self.assertIn('&lt;script&gt;', body)

    def test_get_not_allowed(self):
        response = self.url_open('/converza/audit')
        self.assertNotEqual(response.status_code, 200)
