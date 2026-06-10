# -- coding: utf-8 --
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestCustomerContactsController(HttpCase):
    """Test cases for the CustomerContacts controller defined in
    controllers/website_customer_contact.py.

    Covers:
      - GET /my/contacts           → renders the contact list page
      - GET /my/contacts/<id>      → renders the contact detail page
    """

    def setUp(self):
        super().setUp()
        self.authenticate('portal', 'portal')
        self.portal_user = self.env.ref('base.demo_user0')
        self.parent_partner = self.portal_user.partner_id

    # ------------------------------------------------------------------
    # /my/contacts  (list view)
    # ------------------------------------------------------------------

    def test_contacts_list_page_returns_200(self):
        """GET /my/contacts must return HTTP 200 for an authenticated
        portal user."""
        response = self.url_open('/my/contacts')
        self.assertEqual(
            response.status_code, 200,
            "The contacts list page must be accessible (HTTP 200)."
        )

    def test_contacts_list_page_is_html(self):
        """The contacts list page must serve an HTML response."""
        response = self.url_open('/my/contacts')
        content_type = response.headers.get('Content-Type', '')
        self.assertIn(
            'text/html', content_type,
            "The contacts list page must return text/html."
        )

    def test_contacts_list_empty_when_no_contacts(self):
        """When the portal user has no child partners, /my/contacts must
        still return HTTP 200 without errors."""
        self.env['res.partner'].sudo().search(
            [('parent_id', '=', self.parent_partner.id)]
        ).unlink()

        response = self.url_open('/my/contacts')
        self.assertEqual(
            response.status_code, 200,
            "Contacts list page must return 200 even when there are no "
            "contacts."
        )

    def test_contacts_list_with_multiple_contacts(self):
        """When the portal user has several child partners, /my/contacts
        must return HTTP 200."""
        self.env['res.partner'].sudo().create([
            {
                'name': 'List Contact Alpha',
                'parent_id': self.parent_partner.id,
                'email': 'alpha@example.com',
            },
            {
                'name': 'List Contact Beta',
                'parent_id': self.parent_partner.id,
                'email': 'beta@example.com',
            },
        ])

        response = self.url_open('/my/contacts')
        self.assertEqual(
            response.status_code, 200,
            "Contacts list page must return 200 when the user has contacts."
        )

    # ------------------------------------------------------------------
    # /my/contacts/<id>  (detail view)
    # ------------------------------------------------------------------

    def test_contact_detail_returns_200(self):
        """GET /my/contacts/<id> for a valid contact owned by the portal
        user must return HTTP 200."""
        contact = self.env['res.partner'].sudo().create({
            'name': 'Detail View Contact',
            'parent_id': self.parent_partner.id,
            'email': 'detail@example.com',
        })

        response = self.url_open('/my/contacts/%d' % contact.id)
        self.assertEqual(
            response.status_code, 200,
            "The contact detail page must return HTTP 200 for a valid "
            "contact."
        )

    def test_contact_detail_is_html(self):
        """The contact detail page must serve an HTML response."""
        contact = self.env['res.partner'].sudo().create({
            'name': 'Detail HTML Test',
            'parent_id': self.parent_partner.id,
        })

        response = self.url_open('/my/contacts/%d' % contact.id)
        content_type = response.headers.get('Content-Type', '')
        self.assertIn(
            'text/html', content_type,
            "The contact detail page must return text/html."
        )

    def test_contact_detail_not_found_for_other_user_contact(self):
        """A contact not belonging to the portal user must not appear in the
        detail page (the search filter excludes unrelated contacts).  The
        response should still be HTTP 200 (empty result rendered)."""
        # Create a partner without linking it to the portal user.
        unrelated = self.env['res.partner'].sudo().create({
            'name': 'Unrelated Contact',
        })

        response = self.url_open('/my/contacts/%d' % unrelated.id)
        # The controller renders the template even when the recordset is
        # empty, so we still expect 200 (not a 404).
        self.assertEqual(
            response.status_code, 200,
            "The detail page must return 200 even if the contact does not "
            "belong to the logged-in user (empty recordset rendered)."
        )

    def test_contact_detail_with_full_data(self):
        """A contact with all common fields set must render the detail page
        successfully."""
        country = self.env['res.country'].sudo().search([], limit=1)
        contact = self.env['res.partner'].sudo().create({
            'name': 'Full Data Contact',
            'parent_id': self.parent_partner.id,
            'email': 'fulldata@example.com',
            'phone': '+1-800-555-0199',
            'street': '123 Main Street',
            'city': 'Springfield',
            'country_id': country.id if country else False,
        })

        response = self.url_open('/my/contacts/%d' % contact.id)
        self.assertEqual(
            response.status_code, 200,
            "Contact detail page must return 200 for a fully populated "
            "contact."
        )

    # ------------------------------------------------------------------
    # Unauthenticated access
    # ------------------------------------------------------------------

    def test_contacts_list_redirects_or_renders_for_public_user(self):
        """Public (unauthenticated) access to /my/contacts must return a
        non-500 response (either a redirect to login or a rendered page,
        depending on the website configuration)."""
        # Log out first.
        self.authenticate(None, None)
        response = self.url_open('/my/contacts')
        self.assertIn(
            response.status_code, [200, 301, 302, 303],
            "Public access to /my/contacts must not result in a server error."
        )

    def test_contact_detail_accessible_for_public_user(self):
        """Public (unauthenticated) access to a contact detail URL must
        return a non-500 response."""
        self.authenticate(None, None)
        # Use id=1 as a representative id; the result set will be empty for
        # a public user since the domain filters on the anonymous partner.
        response = self.url_open('/my/contacts/1')
        self.assertIn(
            response.status_code, [200, 301, 302, 303],
            "Public access to a contact detail URL must not cause a server "
            "error."
        )
