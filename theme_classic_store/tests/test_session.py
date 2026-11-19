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

from odoo.tests import tagged

from .common import ClassicStoreHttpCase


@tagged('post_install', '-at_install')
class TestClassicStoreSession(ClassicStoreHttpCase):

    def test_header_logout_is_post_form(self):
        """Odoo 20 only accepts POST on /web/session/logout: the header
        must use a form with a CSRF token, not a plain link."""
        self.authenticate('admin', 'admin')
        doc = self.get_html('/shop')
        forms = doc.xpath("//form[contains(@action, '/web/session/logout')]")
        self.assertTrue(forms, "Logout form not found in the header")
        self.assertEqual(forms[0].get('method', '').upper(), 'POST')
        self.assertTrue(forms[0].xpath(".//input[@name='csrf_token']"))
        self.assertFalse(
            doc.xpath("//a[contains(@href, '/web/session/logout')]"),
            "Logout must not be a GET link")

    def test_logout_post_works(self):
        self.authenticate('admin', 'admin')
        response = self.url_open(
            '/web/session/logout?redirect=/',
            data={'csrf_token': self.csrf_token()})
        self.assertEqual(response.status_code, 200)
        # after logout the public "Sign in" link is shown again
        doc = self.get_html('/shop')
        self.assertFalse(
            doc.xpath("//form[contains(@action, '/web/session/logout')]"))
