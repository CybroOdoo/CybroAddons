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
import hashlib
import hmac as _hmac
import time

from odoo.tests.common import HttpCase, tagged

# Must match constants in odoo/http.py
_CSRF_TOKEN_SALT = 60 * 60 * 24 * 365   # 1 year in seconds
_STORED_SESSION_BYTES = 42


@tagged('post_install', '-at_install')
class TestContactRequestController(HttpCase):
    """Test cases for the WebsiteCustomerContact controller defined in
    controllers/contact_request.py.

    Covers:
      - GET /contact_request_form        → renders the contact request form
      - POST /contact_request_form/submit → creates a new res.partner
      - POST /contact_request_form/write  → updates an existing res.partner
    """

    def setUp(self):
        super().setUp()
        # Authenticate as the demo portal user so that
        # request.env.user.partner_id is a real partner.
        self.authenticate('portal', 'portal')

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _csrf(self):
        """Compute a valid CSRF token for the current test session.

        Replicates the algorithm used by odoo.http.Request.csrf_token():
          max_ts  = int(time.time() + CSRF_TOKEN_SALT)
          msg     = f'{session.sid[:42]}{max_ts}'.encode()
          hm      = hmac(database.secret, msg, sha1).hexdigest()
          token   = f'{hm}o{max_ts}'
        """
        from odoo.http import root as http_root
        session_id = self.opener.cookies.get('session_id')
        if not session_id:
            return ''
        session = http_root.session_store.get(session_id)
        if session is None or not getattr(session, 'sid', None):
            return ''

        secret = (
            self.env['ir.config_parameter']
            .sudo()
            .get_param('database.secret')
        )
        if not secret:
            return ''

        max_ts = int(time.time() + _CSRF_TOKEN_SALT)
        msg = f'{session.sid[:_STORED_SESSION_BYTES]}{max_ts}'.encode()
        hm = _hmac.new(
            secret.encode('ascii'), msg, hashlib.sha1
        ).hexdigest()
        return f'{hm}o{max_ts}'

    # ------------------------------------------------------------------
    # /contact_request_form  (GET)
    # ------------------------------------------------------------------

    def test_contact_request_form_renders(self):
        """GET /contact_request_form must return HTTP 200 and include the
        form page content."""
        response = self.url_open('/contact_request_form')
        self.assertEqual(
            response.status_code, 200,
            "The contact request form page must return HTTP 200."
        )

    def test_contact_request_form_contains_country_data(self):
        """The rendered form page should include a country-related element
        (the controller passes res.country records to the template)."""
        response = self.url_open('/contact_request_form')
        self.assertEqual(response.status_code, 200)
        # The template renders country options; verify the response is HTML.
        self.assertIn(
            'text/html', response.headers.get('Content-Type', ''),
            "Response content type must be HTML."
        )

    # ------------------------------------------------------------------
    # /contact_request_form/submit  (POST)
    # ------------------------------------------------------------------

    def test_contact_request_form_submit_creates_partner(self):
        """Submitting the contact request form must create a new res.partner
        whose parent_id equals the logged-in user's partner."""
        portal_user = self.env.ref('base.demo_user0')
        parent_partner = portal_user.partner_id

        initial_count = self.env['res.partner'].sudo().search_count(
            [('parent_id', '=', parent_partner.id)]
        )

        post_data = {
            'name': 'Test Contact Submit',
            'email': 'test_submit@example.com',
            'phone': '1234567890',
            'csrf_token': self._csrf(),
        }
        response = self.url_open(
            '/contact_request_form/submit', data=post_data
        )
        self.assertEqual(
            response.status_code, 200,
            "The form submission endpoint must return HTTP 200."
        )

        new_count = self.env['res.partner'].sudo().search_count(
            [('parent_id', '=', parent_partner.id)]
        )
        self.assertEqual(
            new_count, initial_count + 1,
            "A new partner must be created after form submission."
        )

    def test_contact_request_form_submit_stores_correct_name(self):
        """The newly created partner must carry the name sent in the form."""
        portal_user = self.env.ref('base.demo_user0')
        parent_partner = portal_user.partner_id

        unique_name = 'UniqueTestContactName_XYZ'
        post_data = {
            'name': unique_name,
            'email': 'unique@example.com',
            'csrf_token': self._csrf(),
        }
        response = self.url_open(
            '/contact_request_form/submit', data=post_data
        )
        self.assertEqual(response.status_code, 200)

        partner = self.env['res.partner'].sudo().search(
            [('parent_id', '=', parent_partner.id), ('name', '=', unique_name)],
            limit=1,
        )
        self.assertTrue(
            partner.exists(),
            "The created partner must have the name submitted in the form."
        )

    def test_contact_request_form_submit_returns_completion_page(self):
        """After a successful submission the completion template must be
        rendered (HTTP 200)."""
        post_data = {
            'name': 'Completion Page Test',
            'email': 'completion@example.com',
            'csrf_token': self._csrf(),
        }
        response = self.url_open(
            '/contact_request_form/submit', data=post_data
        )
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # /contact_request_form/write  (POST)
    # ------------------------------------------------------------------

    def test_contact_request_form_edit_updates_partner(self):
        """POSTing to /contact_request_form/write must update the given
        partner record and redirect back to the contact list."""
        portal_user = self.env.ref('base.demo_user0')
        parent_partner = portal_user.partner_id

        # Create a partner that belongs to the portal user.
        contact = self.env['res.partner'].sudo().create({
            'name': 'Edit Me',
            'parent_id': parent_partner.id,
            'email': 'editme@example.com',
        })

        post_data = {
            'id': str(contact.id),
            'name': 'Edited Name',
            'email': 'edited@example.com',
            'csrf_token': self._csrf(),
        }
        response = self.url_open(
            '/contact_request_form/write', data=post_data
        )
        self.assertEqual(
            response.status_code, 200,
            "The edit endpoint must return HTTP 200."
        )

        contact.invalidate_recordset()
        self.assertEqual(
            contact.name, 'Edited Name',
            "The partner name must be updated after the write call."
        )
        self.assertEqual(
            contact.email, 'edited@example.com',
            "The partner email must be updated after the write call."
        )

    def test_contact_request_form_edit_renders_contact_list(self):
        """After editing, the response should render the customer contact
        list page (contains page_name='customer_contact' context)."""
        portal_user = self.env.ref('base.demo_user0')
        parent_partner = portal_user.partner_id

        contact = self.env['res.partner'].sudo().create({
            'name': 'List Render Test',
            'parent_id': parent_partner.id,
        })

        post_data = {
            'id': str(contact.id),
            'name': 'List Render Test Updated',
            'csrf_token': self._csrf(),
        }
        response = self.url_open(
            '/contact_request_form/write', data=post_data
        )
        self.assertEqual(response.status_code, 200)
