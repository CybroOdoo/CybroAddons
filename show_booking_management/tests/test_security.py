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
import re
from datetime import timedelta

from odoo import Command
from odoo.tests import HttpCase, tagged

from .common import ShowBookingWorldMixin


@tagged('post_install', '-at_install')
class TestBookingSecurity(ShowBookingWorldMixin, HttpCase):
    """ Booking is reserved to logged-in users of the show groups: visitors are
    redirected to the login page, other users are refused, nothing posted is
    trusted, and a draft registration can only be taken over with write access. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_show_world()
        cls.date = cls.today + timedelta(days=1)
        cls.customer = cls.env['res.partner'].create({'name': 'Draft Customer'})
        cls.draft = cls.env['movie.registration'].create({
            'partner_id': cls.customer.id, 'movie_id': cls.movie.id, 'date': cls.date,
            'time_slot_id': cls.slot_1.id, 'screen_id': cls.screen.id})
        # A show that exists but is not open for booking, on its own screen
        cls.other_screen = cls.env['movie.screen'].create({
            'name': 'Other Screen', 'total_rows': 2, 'no_of_seat_row': 2})
        cls.draft_movie = cls.env['movie.movie'].create({
            'name': 'Draft Movie', 'release_date': cls.today - timedelta(days=3),
            'show_start_date': cls.today, 'show_end_date': cls.today + timedelta(days=30),
            'price': 50.0, 'available_screens_ids': [Command.link(cls.other_screen.id)],
            'available_time_slots_ids': [Command.link(cls.slot_1.id)],
        })

    # -- helpers ---------------------------------------------------------------
    def _csrf_token(self):
        """ The CSRF token of the current session (any logged-in page has one). """
        page = self.url_open('/my/account')
        return re.search(r'name="csrf_token"\s+value="([^"]+)"', page.text).group(1)

    def _booking(self, **overrides):
        data = {
            'movie_id': self.movie.id, 'screen_id': self.screen.id,
            'time_slot_id': self.slot_1.id, 'booking_date': str(self.date),
            'registration_id': '', 'selected_seats': ['R1C1'],
        }
        data.update(overrides)
        return data

    def _confirm(self, **overrides):
        data = self._booking(**overrides)
        data['csrf_token'] = self._csrf_token()
        return self.url_open('/movie/confirm_booking', data=data, allow_redirects=False)

    def _all_routes(self):
        """ The four booking routes, as callables returning the response. """
        seat_form = {'movie_id': self.movie.id, 'screen': self.screen.id,
                     'time_slots': self.slot_1.id, 'show_date': str(self.date)}
        return {
            '/show': lambda: self.url_open('/show', allow_redirects=False),
            '/book_now': lambda: self.url_open('/book_now/%s' % self.movie.id, allow_redirects=False),
            '/movie/book_ticket': lambda: self.url_open(
                '/movie/book_ticket', data=seat_form, allow_redirects=False),
            '/movie/confirm_booking': lambda: self._confirm(),
        }

    def _invoices(self):
        return self.env['account.move'].search([('movie_booking_data', '!=', False)])

    # -- who can book -------------------------------------------------------------
    def test_visitors_are_redirected_to_the_login_page(self):
        for route in ('/show', '/book_now/%s' % self.movie.id):
            with self.subTest(route):
                response = self.url_open(route, allow_redirects=False)
                self.assertEqual(response.status_code, 303)
                self.assertIn('/web/login', response.headers['Location'])
        for route in ('/movie/book_ticket', '/movie/confirm_booking'):
            with self.subTest(route):
                response = self.url_open(route, data=self._booking(), allow_redirects=False)
                self.assertNotEqual(response.status_code, 200)
                self.assertFalse(self._invoices())
        response = self.url_open('/movie/book_ticket', data={
            'movie_id': self.movie.id, 'screen': self.screen.id,
            'time_slots': self.slot_1.id, 'show_date': str(self.date)}, allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('/web/login', response.headers['Location'])

    def test_users_outside_the_show_groups_are_refused(self):
        for login in (self.portal_login, self.internal_login):
            self.authenticate(login, login)
            for label, call in self._all_routes().items():
                with self.subTest(user=login, route=label):
                    self.assertEqual(call().status_code, 403)
        self.assertFalse(self._invoices(), "Nothing was invoiced")

    def test_staff_can_book(self):
        """ Control for the two tests above: same routes, right group. """
        self.authenticate(self.staff_login, self.staff_login)
        for label, call in self._all_routes().items():
            with self.subTest(route=label):
                self.assertIn(call().status_code, (200, 303))
        self.assertEqual(len(self._invoices()), 1)

    # -- nothing posted is trusted ---------------------------------------------------
    def test_confirm_booking_rejects_bad_input(self):
        self.authenticate(self.staff_login, self.staff_login)
        self._book_seat('R1C1', self.slot_1, self.date)
        cases = {
            'no seat': dict(selected_seats=[]),
            'malformed seat': dict(selected_seats=['A1']),
            'seat off the chart': dict(selected_seats=['R9C9']),
            'duplicated seat': dict(selected_seats=['R2C1', 'R2C1']),
            'seat already taken': dict(selected_seats=['R1C1']),
            'screen of another show': dict(screen_id=self.other_screen.id, selected_seats=['R1C1']),
            'time slot not of the show': dict(time_slot_id=self.env['time.slots'].create(
                {'movie_time': '23:00'}).id, selected_seats=['R2C2']),
            'past date': dict(booking_date=str(self.today - timedelta(days=1)), selected_seats=['R2C2']),
            'date outside the show': dict(booking_date=str(self.today + timedelta(days=90)),
                                          selected_seats=['R2C2']),
            'not a date': dict(booking_date='tomorrow', selected_seats=['R2C2']),
            'show not open': dict(movie_id=self.draft_movie.id, screen_id=self.other_screen.id,
                                  selected_seats=['R1C1']),
            'garbage ids': dict(movie_id='abc', screen_id='x', time_slot_id='', selected_seats=['R2C2']),
            'unknown show': dict(movie_id=999999, selected_seats=['R2C2']),
        }
        for label, overrides in cases.items():
            with self.subTest(label):
                self.assertEqual(self._confirm(**overrides).status_code, 400, label)
        self.assertFalse(self._invoices(), "Nothing invalid was invoiced")
        response = self._confirm(selected_seats=['R3C3', 'R3C4'])
        self.assertEqual(response.status_code, 303, "A valid booking still works")
        invoice = self._invoices()
        self.assertEqual(invoice.amount_untaxed, 200.0, "Priced by the show, per seat")
        self.assertEqual(invoice.movie_booking_data['selected_seats'], ['R3C3', 'R3C4'])

    def test_unknown_or_garbage_ids_on_the_page_routes(self):
        self.authenticate(self.staff_login, self.staff_login)
        self.assertEqual(self.url_open('/book_now/999999').status_code, 404)
        self.assertEqual(self.url_open('/movie/book_ticket', data={
            'movie_id': 'abc', 'screen': 1, 'time_slots': 1, 'show_date': str(self.date)}).status_code, 400)
        self.assertEqual(self.url_open('/movie/book_ticket', data={
            'movie_id': 999999, 'screen': self.screen.id, 'time_slots': self.slot_1.id,
            'show_date': str(self.date)}).status_code, 404)
        page = self.url_open('/movie/book_ticket', data={
            'movie_id': self.movie.id, 'screen': self.screen.id, 'time_slots': self.slot_1.id,
            'show_date': str(self.date), 'registration_id': '<script>x</script>'})
        self.assertEqual(page.status_code, 400, "Only a number is echoed back into the page")

    # -- taking over a draft registration ----------------------------------------------
    def test_staff_completes_a_draft_and_the_registration_keeps_its_partner(self):
        self.authenticate(self.staff_login, self.staff_login)
        response = self._confirm(registration_id=str(self.draft.id), selected_seats=['R2C1'])
        self.assertEqual(response.status_code, 303)
        invoice = self._invoices()
        self.assertEqual(invoice.partner_id, self.staff.partner_id, "The invoice goes to the logged-in user")
        self.assertEqual(invoice.movie_booking_data['registration_id'], self.draft.id)
        self.assertEqual(self.draft.partner_id, self.customer, "The draft keeps its partner")

    def test_user_without_write_access_cannot_take_over_a_draft(self):
        self.env.ref('show_booking_management.access_movie_registration_user').write({'operation': 'cr'})
        self.authenticate(self.staff_login, self.staff_login)
        response = self._confirm(registration_id=str(self.draft.id), selected_seats=['R2C1'])
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self._invoices())
        # Same user, same seats, without the draft: allowed
        self.assertEqual(self._confirm(selected_seats=['R2C1']).status_code, 303)

    def test_only_a_draft_registration_can_be_completed(self):
        self.authenticate(self.staff_login, self.staff_login)
        invoiced = self._book_seat('R4C4', self.slot_2, self.date)
        for label, registration_id in (('already invoiced', invoiced.id), ('unknown', 999999)):
            with self.subTest(label):
                response = self._confirm(registration_id=str(registration_id), selected_seats=['R2C1'])
                self.assertEqual(response.status_code, 400)
        self.assertFalse(self._invoices())
        self.assertEqual(invoiced.state, 'invoiced')
        self.assertEqual(len(invoiced.seat_ids), 1, "Its seats are untouched")

    # -- the backend side of the same ACL -------------------------------------------------
    def test_show_users_can_create_registrations_in_the_backend(self):
        """ A user of the show group creates a booking by hand (Show Bookings menu):
        the sequence and the record must be reachable with the group's own rights. """
        registration = self.env['movie.registration'].with_user(self.staff).create({
            'partner_id': self.customer.id, 'movie_id': self.movie.id, 'date': self.date,
            'time_slot_id': self.slot_2.id, 'screen_id': self.screen.id})
        self.assertNotEqual(registration.name, 'New')
        self.assertEqual(registration.state, 'draft')
