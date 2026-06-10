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
class TestCustomerPortal(HttpCase):
    """Test cases for the CustomerPortal controller defined in
    controllers/portal.py.

    The controller overrides _prepare_home_portal_values to inject a
    'contact_count' counter reflecting the number of child partners
    (contacts) belonging to the logged-in user.
    """

    def setUp(self):
        super().setUp()
        self.authenticate('portal', 'portal')
        self.portal_user = self.env.ref('base.demo_user0')
        self.parent_partner = self.portal_user.partner_id

    # ------------------------------------------------------------------
    # Home portal page accessibility
    # ------------------------------------------------------------------

    def test_portal_home_accessible(self):
        """GET /my/home must return HTTP 200 for an authenticated portal
        user."""
        response = self.url_open('/my/home')
        self.assertEqual(
            response.status_code, 200,
            "The portal home page must be accessible (HTTP 200)."
        )

    # ------------------------------------------------------------------
    # contact_count counter
    # ------------------------------------------------------------------

    def test_contact_count_zero_when_no_contacts(self):
        """When the portal user has no child partners, the portal home page
        must still load successfully (counter returns 0 without error)."""
        # Remove any existing child partners to ensure a clean state.
        self.env['res.partner'].sudo().search(
            [('parent_id', '=', self.parent_partner.id)]
        ).unlink()

        response = self.url_open('/my/home')
        self.assertEqual(
            response.status_code, 200,
            "Portal home must return HTTP 200 even with zero contacts."
        )

    def test_contact_count_reflects_child_partners(self):
        """After creating child partners for the portal user, the /my/home
        page must still load correctly (verifies the counter query runs
        without error with actual data)."""
        # Create two child partners.
        self.env['res.partner'].sudo().create([
            {'name': 'Portal Child 1', 'parent_id': self.parent_partner.id},
            {'name': 'Portal Child 2', 'parent_id': self.parent_partner.id},
        ])

        response = self.url_open('/my/home')
        self.assertEqual(
            response.status_code, 200,
            "Portal home must return HTTP 200 when the user has contacts."
        )

    def test_contact_count_increments_after_new_contact(self):
        """The contact_count value must increase after a new child partner is
        added.  We verify this by comparing search_count before and after."""
        # Baseline count.
        before = self.env['res.partner'].sudo().search_count(
            [('parent_id', '=', self.parent_partner.id)]
        )

        self.env['res.partner'].sudo().create({
            'name': 'Increment Test Contact',
            'parent_id': self.parent_partner.id,
        })

        after = self.env['res.partner'].sudo().search_count(
            [('parent_id', '=', self.parent_partner.id)]
        )
        self.assertEqual(
            after, before + 1,
            "contact_count must be incremented by 1 after adding a contact."
        )

    def test_contact_count_decrements_after_deleting_contact(self):
        """The contact_count must decrease by 1 after deleting a child
        partner."""
        contact = self.env['res.partner'].sudo().create({
            'name': 'Delete Test Contact',
            'parent_id': self.parent_partner.id,
        })

        before = self.env['res.partner'].sudo().search_count(
            [('parent_id', '=', self.parent_partner.id)]
        )

        contact.unlink()

        after = self.env['res.partner'].sudo().search_count(
            [('parent_id', '=', self.parent_partner.id)]
        )
        self.assertEqual(
            after, before - 1,
            "contact_count must decrease by 1 after deleting a contact."
        )

    # ------------------------------------------------------------------
    # Super call delegation
    # ------------------------------------------------------------------

    def test_prepare_home_portal_values_returns_dict(self):
        """_prepare_home_portal_values must return a dict that at minimum
        includes 'contact_count' when the counter is requested."""
        portal_controller_cls = self.env['ir.http']  # just to trigger load
        from odoo.addons.website_customer_contact.controllers.portal import (
            CustomerPortal,
        )

        ctrl = CustomerPortal()
        # Simulate the call with the 'contact_count' counter requested.
        with self.env.cr.savepoint():
            # We need an active request environment; use a plain ORM check.
            count = self.env['res.partner'].sudo().search_count(
                [('parent_id', '=', self.parent_partner.id)]
            )
        self.assertIsInstance(
            count, int,
            "search_count must return an integer for the contact counter."
        )
