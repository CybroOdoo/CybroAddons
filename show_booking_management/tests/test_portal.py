# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import HttpCase, tagged

from .common import ShowBookingWorldMixin


@tagged('post_install', '-at_install')
class TestPortal(ShowBookingWorldMixin, HttpCase):
    """ Portal users read their own registrations only: the ir.access row, the
    /my/shows list, the home counter and the home card. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_show_world()
        cls.other_portal = cls.env['res.users'].create({
            'name': 'Other Portal Customer', 'login': 'show_booking_portal_2',
            'password': 'show_booking_portal_2',
            'group_ids': [Command.set([cls.env.ref('base.group_portal').id])],
        })
        cls.empty_portal = cls.env['res.users'].create({
            'name': 'Portal Without Booking', 'login': 'show_booking_portal_empty',
            'password': 'show_booking_portal_empty',
            'group_ids': [Command.set([cls.env.ref('base.group_portal').id])],
        })
        cls.empty_staff = cls.env['res.users'].create({
            'name': 'Staff Without Booking', 'login': 'show_booking_staff_empty',
            'password': 'show_booking_staff_empty',
            'group_ids': [Command.link(cls.env.ref(
                'show_booking_management.show_booking_management_group_user').id)],
        })
        cls.sysadmin = cls.env['res.users'].create({
            'name': 'System Admin Probe', 'login': 'show_booking_sysadmin',
            'password': 'show_booking_sysadmin',
            'group_ids': [Command.set([cls.env.ref('base.group_system').id])],
        })
        cls.own = cls._ticket(cls.portal_user.partner_id, 'R1C1')
        cls.theirs = cls._ticket(cls.other_portal.partner_id, 'R1C2')
        cls.staffs = cls._ticket(cls.staff.partner_id, 'R1C3')

    @classmethod
    def _ticket(cls, partner, seat):
        ticket = cls.env['movie.registration'].create({
            'partner_id': partner.id, 'movie_id': cls.movie.id, 'date': cls.today,
            'time_slot_id': cls.slot_1.id, 'screen_id': cls.screen.id,
            'no_of_tickets': 1, 'state': 'invoiced'})
        cls.env['movie.seats'].create({
            'screen_id': cls.screen.id, 'time_slot_id': cls.slot_1.id, 'date': cls.today,
            'movie_registration_id': ticket.id, 'seat': seat, 'is_booked': True})
        return ticket

    def _counter(self, login):
        self.authenticate(login, login)
        return self.make_jsonrpc_request(
            '/my/counters', {'counters': {'shows_count': 'client_category'}})['shows_count']

    # -- the ir.access row -----------------------------------------------------------
    def test_portal_user_reads_only_own_registrations(self):
        Registration = self.env['movie.registration'].with_user(self.portal_user)
        self.assertEqual(Registration.search([]), self.own)
        with self.assertRaises(AccessError):
            self.theirs.with_user(self.portal_user).read(['name'])

    def test_portal_user_cannot_write_create_or_delete(self):
        own = self.own.with_user(self.portal_user)
        with self.assertRaises(AccessError):
            own.write({'no_of_tickets': 5})
        with self.assertRaises(AccessError):
            own.unlink()
        with self.assertRaises(AccessError):
            self.env['movie.registration'].with_user(self.portal_user).create({
                'partner_id': self.portal_user.partner_id.id, 'movie_id': self.movie.id,
                'date': self.today, 'time_slot_id': self.slot_1.id, 'screen_id': self.screen.id})

    def test_portal_user_cannot_browse_the_catalogue(self):
        with self.assertRaises(AccessError):
            self.env['movie.movie'].with_user(self.portal_user).search([])
        with self.assertRaises(AccessError):
            self.env['movie.seats'].with_user(self.portal_user).search([])

    # -- /my/shows --------------------------------------------------------------------
    def test_my_shows_lists_only_the_users_own_bookings(self):
        self.authenticate(self.portal_login, self.portal_login)
        page = self.url_open('/my/shows')
        self.assertEqual(page.status_code, 200)
        self.assertIn(self.own.name, page.text)
        self.assertIn('Website Movie', page.text, "The movie name is readable although portal cannot read movies")
        self.assertNotIn(self.theirs.name, page.text)
        self.assertNotIn(self.staffs.name, page.text)

    def test_my_shows_for_staff_is_their_own_bookings_too(self):
        self.authenticate(self.staff_login, self.staff_login)
        page = self.url_open('/my/shows')
        self.assertIn(self.staffs.name, page.text)
        self.assertNotIn(self.own.name, page.text)
        self.assertNotIn(self.theirs.name, page.text)

    def test_my_shows_for_a_system_administrator_lists_all(self):
        self.authenticate('show_booking_sysadmin', 'show_booking_sysadmin')
        page = self.url_open('/my/shows')
        for ticket in (self.own, self.theirs, self.staffs):
            self.assertIn(ticket.name, page.text)

    def test_my_shows_for_a_user_without_access_is_empty_not_an_error(self):
        self.authenticate(self.internal_login, self.internal_login)
        page = self.url_open('/my/shows')
        self.assertEqual(page.status_code, 200)
        self.assertNotIn(self.own.name, page.text)

    def test_my_shows_requires_login(self):
        response = self.url_open('/my/shows', allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('/web/login', response.headers['Location'])

    # -- counter and card -----------------------------------------------------------------
    # The route only needs to know whether there is a matching record
    # (search_count with limit=1), so a leak shows up as 1 instead of 0.
    def test_counter_counts_only_own_registrations(self):
        self.assertEqual(self._counter(self.portal_login), 1)
        self.assertEqual(self._counter('show_booking_portal_empty'), 0,
                         "A customer without booking gets 0 although others have some")

    def test_counter_for_staff_admin_and_users_without_access(self):
        self.assertEqual(self._counter(self.staff_login), 1, "The staff's own booking")
        self.assertEqual(self._counter('show_booking_staff_empty'), 0,
                         "Staff see their own bookings only, not all of them")
        self.assertEqual(self._counter('show_booking_sysadmin'), 1,
                         "The administrator has no booking but sees everybody's")
        self.assertEqual(self._counter(self.internal_login), 0, "No access: 0, not an error")

    def test_home_shows_the_bookings_card(self):
        self.authenticate(self.portal_login, self.portal_login)
        page = self.url_open('/my/home')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Show Bookings', page.text)
        self.assertIn('href="/my/shows"', page.text)
        self.assertIn('shows_count', page.text)
