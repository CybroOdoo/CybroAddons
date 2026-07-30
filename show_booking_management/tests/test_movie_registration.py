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
from datetime import date, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError



class TestMovieRegistration(TransactionCase):
    """Test cases for movie.registration model"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Registration = cls.env['movie.registration']

        cls.screen = cls.env['movie.screen'].create({
            'name': 'Reg Test Screen',
            'total_rows': 5,
            'no_of_seat_row': 10,  # 50 seats total
        })
        cls.time_slot = cls.env['time.slots'].search([('movie_time', '=', '10.00')], limit=1) or cls.env['time.slots'].create({'movie_time': '10:00'})

        cls.today = date.today()
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.next_week = cls.today + timedelta(days=7)

        cls.movie = cls.env['movie.movie'].create({
            'name': 'Reg Test Movie',
            'duration': 2.0,
            'release_date': cls.today,
            'show_start_date': cls.today,
            'show_end_date': cls.next_week,
            'prebooking_slot': 10,
            'price': 200.0,
            'state': 'ongoing',
            'available_screens_ids': [(4, cls.screen.id)],
            'available_time_slots_ids': [(4, cls.time_slot.id)],
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Test Booker'})

    def _make_registration(self, **kwargs):
        """Helper to create a registration with sensible defaults."""
        vals = {
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.time_slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 1,
        }
        vals.update(kwargs)
        return self.Registration.create(vals)

    # ── Creation ──────────────────────────────────────────────────────────────

    def test_registration_sequence_assigned(self):
        """Name must be a sequence value, not the default 'New'"""
        reg = self._make_registration()
        self.assertNotEqual(reg.name, 'New')
        self.assertTrue(reg.name)

    def test_registration_defaults(self):
        """Default state is draft, currency is company currency"""
        reg = self._make_registration()
        self.assertEqual(reg.state, 'draft')
        self.assertEqual(reg.currency_id, self.env.user.company_id.currency_id)

    # ── Computed fields ───────────────────────────────────────────────────────

    def test_available_time_slot_ids_computed(self):
        """available_time_slot_ids contains time slots of the linked movie"""
        reg = self._make_registration()
        self.assertIn(self.time_slot.id, reg.available_time_slot_ids.ids)

    def test_available_screens_ids_computed(self):
        """available_screens_ids contains screens of the linked movie"""
        reg = self._make_registration()
        self.assertIn(self.screen.id, reg.available_screens_ids.ids)

    def test_related_movie_price(self):
        """movie_price is the related price from the movie"""
        reg = self._make_registration()
        self.assertEqual(reg.movie_price, self.movie.price)

    # ── fetch_movies onchange ─────────────────────────────────────────────────

    def test_fetch_movies_populates_available_movies(self):
        """fetch_movies populates available_movie_ids for a valid today date"""
        reg = self.Registration.new({'date': self.today})
        reg.fetch_movies()
        self.assertIn(self.movie.id, reg.available_movie_ids.ids)

    def test_fetch_movies_past_date_raises(self):
        """fetch_movies raises ValidationError for a past date"""
        reg = self.Registration.new({'date': self.today - timedelta(days=1)})
        with self.assertRaises(ValidationError):
            reg.fetch_movies()

    def test_fetch_movies_resets_movie_id(self):
        """fetch_movies clears movie_id when date changes"""
        reg = self.Registration.new({
            'date': self.today,
            'movie_id': self.movie.id,
        })
        reg.fetch_movies()
        self.assertFalse(reg.movie_id)

    # ── set_values onchange ───────────────────────────────────────────────────

    def test_set_values_clears_slot_and_screen(self):
        """set_values (movie_id onchange) clears time_slot_id and screen_id"""
        reg = self.Registration.new({
            'movie_id': self.movie.id,
            'time_slot_id': self.time_slot.id,
            'screen_id': self.screen.id,
        })
        reg.set_values()
        self.assertFalse(reg.time_slot_id)
        self.assertFalse(reg.screen_id)

    # ── Constraints ───────────────────────────────────────────────────────────

    def test_zero_tickets_raises(self):
        """Creating registration with 0 tickets raises ValidationError"""
        with self.assertRaises(ValidationError):
            self._make_registration(no_of_tickets=0)

    def test_negative_tickets_raises(self):
        """Creating registration with negative tickets raises ValidationError"""
        with self.assertRaises(ValidationError):
            self._make_registration(no_of_tickets=-1)

    def test_seat_count_mismatch_raises(self):
        """seat_ids count != no_of_tickets raises ValidationError"""
        reg = self._make_registration(no_of_tickets=2)
        with self.assertRaises(ValidationError):
            reg.write({
                'seat_ids': [(0, 0, {
                    'screen_id': self.screen.id,
                    'time_slot_id': self.time_slot.id,
                    'date': self.today,
                    'seat': 'A1',
                    'is_booked': True,
                })],
            })

    # ── Seat availability ─────────────────────────────────────────────────────

    def test_exceeding_screen_capacity_raises(self):
        """Booking more than screen.total_seat_count raises ValidationError"""
        with self.assertRaises(ValidationError):
            self._make_registration(no_of_tickets=51)  # screen has 50 seats

    def test_prebooking_limit_enforced(self):
        """Exceeding prebooking_slot during prebooking state raises ValidationError"""
        self.movie.write({'state': 'prebooking', 'prebooking_slot': 2})
        # First registration: 1 ticket (invoiced, counts toward limit)
        reg1 = self._make_registration(no_of_tickets=1)
        reg1.write({'state': 'invoiced'})
        # Second registration: 2 more tickets → total 3 > prebooking_slot 2
        with self.assertRaises(ValidationError):
            self._make_registration(no_of_tickets=2)
        # Restore state
        self.movie.write({'state': 'ongoing'})

    def test_booking_within_capacity_succeeds(self):
        """Valid booking within capacity succeeds"""
        reg = self._make_registration(no_of_tickets=5)
        self.assertTrue(reg.id)

    # ── check_seat_available (JS API) ─────────────────────────────────────────

    def test_check_seat_available_fails_when_over_capacity(self):
        """Returns Failed when requested tickets exceed screen capacity"""
        result = self.Registration.check_seat_available(
            self.today, self.time_slot.id, self.screen.id, 60)
        self.assertEqual(result['Status'], 'Failed')
        self.assertIn('seats left', result['Error'])

    def test_check_seat_available_succeeds_within_capacity(self):
        """Returns Success when requested tickets are within capacity"""
        result = self.Registration.check_seat_available(
            self.today, self.time_slot.id, self.screen.id, 2)
        self.assertEqual(result['Status'], 'Success')

    def test_check_seat_available_exact_capacity(self):
        """Returns Success when requested tickets exactly match available seats"""
        result = self.Registration.check_seat_available(
            self.today, self.time_slot.id, self.screen.id, 50)
        self.assertEqual(result['Status'], 'Success')

    def test_check_seat_available_considers_existing_invoiced(self):
        """Already-invoiced bookings reduce available seats"""
        # Book 48 seats as invoiced
        reg = self._make_registration(no_of_tickets=48)
        reg.write({'state': 'invoiced'})
        # 3 more would exceed 50
        result = self.Registration.check_seat_available(
            self.today, self.time_slot.id, self.screen.id, 3)
        self.assertEqual(result['Status'], 'Failed')
        # 2 more is fine
        result2 = self.Registration.check_seat_available(
            self.today, self.time_slot.id, self.screen.id, 2)
        self.assertEqual(result2['Status'], 'Success')

    # ── action_select_seats ───────────────────────────────────────────────────

    def test_action_select_seats_returns_act_url(self):
        """action_select_seats returns an ir.actions.act_url with correct URL"""
        reg = self._make_registration()
        action = reg.action_select_seats()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertIn('/movie/book_ticket', action['url'])
        self.assertIn(f'registration_id={reg.id}', action['url'])
        self.assertIn(f'movie_id={self.movie.id}', action['url'])
        self.assertIn(f'screen={self.screen.id}', action['url'])

    def test_action_select_seats_missing_fields_raises(self):
        """action_select_seats raises ValidationError when required fields missing"""
        reg = self.Registration.new({'partner_id': self.partner.id})
        with self.assertRaises(ValidationError):
            reg.action_select_seats()

    # ── action_open_invoices ──────────────────────────────────────────────────

    def test_action_open_invoices_returns_window_action(self):
        """action_open_invoices returns a window action scoped to this ticket"""
        reg = self._make_registration()
        action = reg.action_open_invoices()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'account.move')
        self.assertIn(('movie_ticket_id', '=', reg.id), action['domain'])
