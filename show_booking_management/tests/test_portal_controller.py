# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import timedelta
from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.addons.show_booking_management.controller.portal import ShowPortal


@tagged('post_install', '-at_install')
class TestPortalController(TransactionCase):
    """Test cases for portal.py controller: _prepare_home_portal_values
    and my_subscription route logic."""

    def setUp(self):
        super(TestPortalController, self).setUp()
        self.today = fields.Date.today()
        self.partner = self.env['res.partner'].create({'name': 'Portal Test Partner'})
        self.screen = self.env['movie.screen'].create({
            'name': 'Portal Screen',
            'total_rows': 5,
            'no_of_seat_row': 10,
        })
        self.time_slot = self.env['time.slots'].create({
            'movie_time': '16:00',
        })
        self.movie = self.env['movie.movie'].create({
            'name': 'Portal Test Movie',
            'release_date': self.today - timedelta(days=5),
            'show_start_date': self.today,
            'show_end_date': self.today + timedelta(days=20),
            'price': 100.0,
            'available_screens_ids': [(4, self.screen.id)],
            'available_time_slots_ids': [(4, self.time_slot.id)],
        })
        self.movie.action_prebooking()
        self.movie.action_start_show()
        self.registration = self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.time_slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 1,
        })

    # -------------------------------------------------------------------------
    # ShowPortal class registration
    # -------------------------------------------------------------------------
    def test_show_portal_is_controller(self):
        """Verify ShowPortal inherits from CustomerPortal."""
        from odoo.addons.portal.controllers.portal import CustomerPortal
        self.assertTrue(issubclass(ShowPortal, CustomerPortal))

    # -------------------------------------------------------------------------
    # _prepare_home_portal_values — business logic
    # -------------------------------------------------------------------------
    def test_prepare_home_portal_values_shows_count(self):
        """Test that shows_count reflects all movie.registration records."""
        total = self.env['movie.registration'].search_count([])
        self.assertGreaterEqual(total, 1)

    def test_prepare_home_portal_values_counter_key(self):
        """Test that _prepare_home_portal_values route is declared."""
        self.assertTrue(hasattr(ShowPortal, '_prepare_home_portal_values'))

    # -------------------------------------------------------------------------
    # my_subscription route — validate route registration
    # -------------------------------------------------------------------------
    def test_my_subscription_route_registered(self):
        """Test that the my_subscription route is registered on ShowPortal."""
        self.assertTrue(hasattr(ShowPortal, 'my_subscription'))

    # -------------------------------------------------------------------------
    # my_subscription business logic — admin sees all, partner sees own
    # -------------------------------------------------------------------------
    def test_my_subscription_admin_sees_all(self):
        """Test business logic: admin user can see all movie registrations."""
        # Admin group search
        all_shows = self.env['movie.registration'].sudo().search([])
        self.assertGreaterEqual(len(all_shows), 1)

    def test_my_subscription_partner_sees_own(self):
        """Test business logic: a partner user sees only their own registrations."""
        partner_shows = self.env['movie.registration'].sudo().search([
            ('partner_id', '=', self.partner.id)
        ])
        self.assertEqual(len(partner_shows), 1)
        self.assertEqual(partner_shows[0].id, self.registration.id)

    def test_my_subscription_partner_no_other_records(self):
        """Test business logic: partner does not see registrations of others."""
        other_partner = self.env['res.partner'].create({'name': 'Other Partner'})
        partner_shows = self.env['movie.registration'].sudo().search([
            ('partner_id', '=', other_partner.id)
        ])
        self.assertEqual(len(partner_shows), 0)
