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
from datetime import timedelta

from odoo import Command, fields

# A valid 1x1 PNG, as the base64 str Binary fields take on write in v20
PNG_1PX = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='


class ShowBookingWorldMixin:
    """ A running show (poster, cast with image, two time slots, a 4x4 screen)
    a staff user allowed to book it on the website and a show administrator. """

    @classmethod
    def _create_show_world(cls):
        today = fields.Date.today()
        cls.today = today
        cls.screen = cls.env['movie.screen'].create({
            'name': 'Screen One', 'total_rows': 4, 'no_of_seat_row': 4})
        cls.slot_1 = cls.env['time.slots'].create({'movie_time': '18:00'})
        cls.slot_2 = cls.env['time.slots'].create({'movie_time': '21:00'})
        cast_type = cls.env['cast.type'].create({'name': 'Actor'})
        cls.cast = cls.env['movie.cast'].create({
            'name': 'Cast Member One', 'cast_id': cast_type.id, 'cast_image': PNG_1PX})
        cls.movie = cls.env['movie.movie'].create({
            'name': 'Website Movie',
            'release_date': today - timedelta(days=3),
            'show_start_date': today,
            'show_end_date': today + timedelta(days=30),
            'price': 100.0,
            'about_movie': 'A movie about testing.',
            'movie_poster': PNG_1PX,
            'movie_cast_ids': [Command.link(cls.cast.id)],
            'available_screens_ids': [Command.link(cls.screen.id)],
            'available_time_slots_ids': [Command.link(cls.slot_1.id), Command.link(cls.slot_2.id)],
        })
        cls.movie.action_prebooking()
        cls.movie.action_start_show()
        group = cls.env.ref('show_booking_management.show_booking_management_group_admin')
        cls.admin_login = 'show_booking_admin'
        cls.show_admin = cls.env['res.users'].create({
            'name': 'Show Booking Admin', 'login': cls.admin_login,
            'password': cls.admin_login, 'email': 'admin.show@example.com',
            'group_ids': [Command.link(group.id)],
        })
        cls.portal_login = 'show_booking_portal'
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Show Portal Customer', 'login': cls.portal_login,
            'password': cls.portal_login,
            'group_ids': [Command.set([cls.env.ref('base.group_portal').id])],
        })
        cls.internal_login = 'show_booking_internal'
        cls.internal_user = cls.env['res.users'].create({
            'name': 'Internal Without Show Group', 'login': cls.internal_login,
            'password': cls.internal_login,
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })
        cls.staff_login = 'show_booking_staff'
        cls.staff = cls.env['res.users'].create({
            'name': 'Show Booking Staff', 'login': cls.staff_login,
            'password': cls.staff_login, 'email': 'staff@example.com',
            'group_ids': [Command.link(cls.env.ref(
                'show_booking_management.show_booking_management_group_user').id)],
        })

    @classmethod
    def _book_seat(cls, seat, slot, date):
        """ Book a seat for someone else (a confirmed ticket). """
        other = cls.env['res.partner'].create({'name': 'Someone Else'})
        ticket = cls.env['movie.registration'].create({
            'partner_id': other.id, 'movie_id': cls.movie.id, 'date': date,
            'time_slot_id': slot.id, 'screen_id': cls.screen.id,
            'no_of_tickets': 1, 'state': 'invoiced'})
        cls.env['movie.seats'].create({
            'screen_id': cls.screen.id, 'time_slot_id': slot.id, 'date': date,
            'movie_registration_id': ticket.id, 'seat': seat, 'is_booked': True})
        return ticket
