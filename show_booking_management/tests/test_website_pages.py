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

from odoo.tests import HttpCase, tagged

from .common import PNG_1PX, ShowBookingWorldMixin


@tagged('post_install', '-at_install')
class TestWebsitePages(ShowBookingWorldMixin, HttpCase):
    """ Really GET/POST every website page of the booking flow. Compile checks do
    not catch a QWeb template that only fails when rendered (v20 turned
    Binary values used as base64 strings into a 500, and t-esc into blanks). """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_show_world()
        cls.date = cls.today + timedelta(days=1)
        cls._book_seat('R1C1', cls.slot_1, cls.date)

    def setUp(self):
        super().setUp()
        self.authenticate(self.staff_login, self.staff_login)

    def _seat_page(self, slot=None, csrf_token=None):
        return self.url_open('/movie/book_ticket', data={
            'movie_id': self.movie.id, 'screen': self.screen.id,
            'time_slots': (slot or self.slot_1).id, 'show_date': str(self.date),
            'registration_id': '',
        })

    def test_show_page_lists_the_running_show(self):
        response = self.url_open('/show')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Website Movie', response.text)
        self.assertIn('/book_now/%s' % self.movie.id, response.text)
        self.assertIn('data:image/png;base64,%s' % PNG_1PX, response.text, "The poster is embedded")

    def test_book_now_page_shows_the_show_and_the_booking_form(self):
        response = self.url_open('/book_now/%s' % self.movie.id)
        self.assertEqual(response.status_code, 200)
        text = response.text
        for expected in ('Website Movie', 'A movie about testing.', 'Cast Member One', 'Actor',
                         'Screen One', '06:00 PM', '09:00 PM', 'choose_date', '/movie/book_ticket'):
            self.assertIn(expected, text)
        self.assertIn('data:image/png;base64,%s' % PNG_1PX, text)

    def test_seat_chart_marks_taken_seats(self):
        response = self._seat_page()
        self.assertEqual(response.status_code, 200)
        text = response.text
        self.assertEqual(len(re.findall(r'class="seat-checkbox"', text)), 16, "4 rows x 4 seats")
        self.assertIn('value="R4C4"', text)
        taken = re.search(r'<input[^>]*value="R1C1"[^>]*>', text).group(0)
        self.assertIn('disabled', taken)
        free = re.search(r'<input[^>]*value="R1C2"[^>]*>', text).group(0)
        self.assertNotIn('disabled', free)
        self.assertRegex(text, r'seat-demo-booked">\s*1\s*<')
        self.assertRegex(text, r'seat-demo-available">\s*15\s*<')
        self.assertIn('Website Movie', text)
        self.assertIn(str(self.date), text)

    def test_confirm_booking_creates_the_invoice_and_redirects_to_it(self):
        page = self._seat_page(slot=self.slot_2)
        token = re.search(r'name="csrf_token"\s+value="([^"]+)"', page.text).group(1)
        response = self.url_open('/movie/confirm_booking', data={
            'csrf_token': token, 'movie_id': self.movie.id, 'screen_id': self.screen.id,
            'time_slot_id': self.slot_2.id, 'booking_date': str(self.date),
            'registration_id': '', 'selected_seats': ['R2C2', 'R2C3'],
        }, allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        invoice = self.env['account.move'].search([('movie_booking_data', '!=', False)])
        self.assertEqual(len(invoice), 1)
        self.assertIn('/my/invoices/%s?' % invoice.id, response.headers['Location'])
        self.assertEqual(invoice.state, 'posted')
        self.assertEqual(invoice.partner_id, self.staff.partner_id)
        self.assertEqual(invoice.amount_untaxed, 200.0)
        self.assertEqual(invoice.movie_booking_data['selected_seats'], ['R2C2', 'R2C3'])
        self.assertEqual(invoice.movie_booking_data['time_slot_id'], self.slot_2.id)
        self.assertFalse(self.env['movie.registration'].search(
            [('partner_id', '=', self.staff.partner_id.id)]), "Nothing is booked before payment")
        invoice_page = self.url_open(response.headers['Location'])
        self.assertEqual(invoice_page.status_code, 200)
        self.assertIn(invoice.name, invoice_page.text)

    def test_frontend_asset_bundle_compiles(self):
        """ The rewritten Interactions are part of web.assets_frontend. """
        js = self.env['ir.qweb']._get_asset_bundle('web.assets_frontend').js()
        self.assertTrue(js)
        content = js.raw.decode()
        for name in ('show_booking_management.BookShow', 'show_booking_management.SelectSeat'):
            self.assertIn(name, content)

    def test_backend_asset_bundle_compiles(self):
        """ The OWL 3 time picker is part of web.assets_backend. """
        js = self.env['ir.qweb']._get_asset_bundle('web.assets_backend').js()
        self.assertTrue(js)
        self.assertIn('timepicker_time', js.raw.decode())
