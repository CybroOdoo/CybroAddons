# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import timedelta

from odoo.tests import HttpCase, tagged

from .common import ShowBookingWorldMixin


@tagged('post_install', '-at_install')
class TestShowBookingTours(ShowBookingWorldMixin, HttpCase):
    """ Drive the rewritten frontend Interactions and the OWL 3 time picker in
    headless Chrome. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_show_world()

    def test_time_picker_widget(self):
        self.start_tour(
            '/odoo/action-show_booking_management.time_slots_action/new',
            'show_booking_time_slot_tour', login=self.admin_login)
        slot = self.env['time.slots'].search([('movie_time', '=', '21.30')])
        self.assertEqual(len(slot), 1)
        self.assertEqual(slot.name, '09:30 PM')

    def test_booking_flow(self):
        tomorrow = self.today + timedelta(days=1)
        self._book_seat('R2C2', self.slot_2, tomorrow)
        self.start_tour('/show', 'show_booking_tour', login=self.staff_login)
        invoice = self.env['account.move'].search([('movie_booking_data', '!=', False)])
        self.assertEqual(len(invoice), 1, "The tour confirmed one booking")
        data = invoice.movie_booking_data
        self.assertEqual(data['selected_seats'], ['R3C2'])
        self.assertEqual(data['time_slot_id'], self.slot_2.id)
        self.assertEqual(data['booking_date'], str(tomorrow))
        self.assertEqual(invoice.partner_id, self.staff.partner_id)
