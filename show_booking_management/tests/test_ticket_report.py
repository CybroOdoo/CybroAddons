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
from odoo.tests import HttpCase, tagged

from .common import PNG_1PX


@tagged('post_install', '-at_install')
class TestTicketReport(HttpCase):
    """ The ticket PDF (QWeb report) and its download route. wkhtmltopdf is not
    run in test mode, so the QWeb output is checked through the HTML renderer
    and the real /report route. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        today = fields.Date.today()
        screen = cls.env['movie.screen'].create({
            'name': 'Screen Report', 'total_rows': 4, 'no_of_seat_row': 4})
        slot = cls.env['time.slots'].create({'movie_time': '20:15'})
        cls.movie = cls.env['movie.movie'].create({
            'name': 'Report Movie',
            'release_date': today - timedelta(days=3),
            'show_start_date': today,
            'show_end_date': today + timedelta(days=5),
            'price': 80.0,
            'movie_poster': PNG_1PX,
            'available_screens_ids': [Command.link(screen.id)],
            'available_time_slots_ids': [Command.link(slot.id)],
        })
        partner = cls.env['res.partner'].create({'name': 'Report Customer'})
        cls.ticket = cls.env['movie.registration'].create({
            'partner_id': partner.id, 'movie_id': cls.movie.id, 'date': today,
            'time_slot_id': slot.id, 'screen_id': screen.id, 'no_of_tickets': 2,
            'state': 'invoiced'})
        cls.env['movie.seats'].create([{
            'screen_id': screen.id, 'time_slot_id': slot.id, 'date': today,
            'movie_registration_id': cls.ticket.id, 'seat': seat, 'is_booked': True,
        } for seat in ('R1C1', 'R1C2')])
        cls.ticket.qr_code = cls.ticket.get_qr_code_image().decode()
        cls.staff = cls.env['res.users'].create({
            'name': 'Show Staff', 'login': 'show_staff_report',
            'password': 'show_staff_report',
            'group_ids': [Command.link(cls.env.ref(
                'show_booking_management.show_booking_management_group_user').id)],
        })

    def test_report_renders_the_ticket_with_a_real_qr_image(self):
        html, _fmt = self.env['ir.actions.report']._render_qweb_html(
            'show_booking_management.action_report_movie_ticket', self.ticket.ids)
        html = html.decode()
        self.assertIn(self.ticket.name, html)
        self.assertIn('Report Movie', html)
        self.assertIn(str(self.ticket.date), html)
        self.assertIn('08:15 PM', html)
        self.assertIn('Screen Report', html)
        self.assertIn('R1C1', html)
        self.assertIn('R1C2', html)
        # base64 of the PNG signature; a Binary value formatted as text is not it
        self.assertIn('data:image/png;base64,iVBORw0KGgo', html)
        self.assertIn('data:image/png;base64,%s' % PNG_1PX, html, "The movie poster is embedded too")

    def test_ticket_download_route(self):
        self.authenticate('show_staff_report', 'show_staff_report')
        response = self.url_open(
            '/report/pdf/show_booking_management.action_report_movie_ticket/%s' % self.ticket.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.ticket.name, response.text)
