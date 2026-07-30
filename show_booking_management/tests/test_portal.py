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
from odoo.tests.common import HttpCase, TransactionCase


class TestShowPortalValues(TransactionCase):
    """
    Unit tests for ShowPortal._prepare_home_portal_values
    (tests the model-level logic without HTTP).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = date.today()
        cls.next_week = cls.today + timedelta(days=7)

        cls.screen = cls.env['movie.screen'].create({
            'name': 'Portal Screen', 'total_rows': 5, 'no_of_seat_row': 5})
        cls.slot = cls.env['time.slots'].search([('movie_time', '=', '11.00')], limit=1) or cls.env['time.slots'].create({'movie_time': '11:00'})
        cls.movie = cls.env['movie.movie'].create({
            'name': 'Portal Test Movie',
            'release_date': cls.today,
            'show_start_date': cls.today,
            'show_end_date': cls.next_week,
            'price': 100.0,
            'state': 'ongoing',
            'available_screens_ids': [(4, cls.screen.id)],
            'available_time_slots_ids': [(4, cls.slot.id)],
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Portal User Partner'})

    def test_registration_search_count_all(self):
        """search_count([]) returns total registration count (admin view)"""
        count_before = self.env['movie.registration'].search_count([])
        self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 1,
        })
        count_after = self.env['movie.registration'].search_count([])
        self.assertEqual(count_after, count_before + 1)

    def test_registration_filter_by_partner(self):
        """Filtering registrations by partner returns only that partner's bookings"""
        partner_a = self.env['res.partner'].create({'name': 'Partner A'})
        partner_b = self.env['res.partner'].create({'name': 'Partner B'})

        self.env['movie.registration'].create({
            'partner_id': partner_a.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 1,
        })
        self.env['movie.registration'].create({
            'partner_id': partner_b.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 1,
        })

        shows_a = self.env['movie.registration'].search(
            [('partner_id', '=', partner_a.id)])
        shows_b = self.env['movie.registration'].search(
            [('partner_id', '=', partner_b.id)])

        self.assertEqual(len(shows_a), 1)
        self.assertEqual(len(shows_b), 1)
        self.assertNotEqual(shows_a.id, shows_b.id)

    def test_registration_state_filter(self):
        """Filtering by invoiced state returns only invoiced registrations"""
        reg = self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 1,
        })
        self.assertEqual(reg.state, 'draft')
        reg.write({'state': 'invoiced'})

        invoiced = self.env['movie.registration'].search([
            ('state', '=', 'invoiced'), ('id', '=', reg.id)])
        self.assertEqual(len(invoiced), 1)

        draft = self.env['movie.registration'].search([
            ('state', '=', 'draft'), ('id', '=', reg.id)])
        self.assertEqual(len(draft), 0)

    def test_portal_route_requires_auth(self):
        """
        /my/shows route is auth='user' — anonymous access is not allowed.
        Verified by confirming the route definition in the controller.
        """
        from odoo.addons.show_booking_management.controller.portal import ShowPortal
        import inspect
        source = inspect.getsource(ShowPortal.my_subscription)
        self.assertIn("auth=\"user\"", source)
