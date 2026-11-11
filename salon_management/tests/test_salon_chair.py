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
#############################################################################
from odoo.tests import tagged

from .common import SalonCommon


@tagged('post_install', '-at_install')
class TestSalonChair(SalonCommon):

    def test_sequence_name(self):
        chair = self.env['salon.chair'].create({'date': self.at()})
        self.assertTrue(chair.name.startswith('CHAIR-'))
        other = self.env['salon.chair'].create({'date': self.at()})
        self.assertNotEqual(chair.name, other.name)

    def test_explicit_name_is_kept(self):
        # Any name other than "New" skips the sequence.
        chair = self.env['salon.chair'].create(
            {'name': 'VIP Chair', 'date': self.at()})
        self.assertEqual(chair.name, 'VIP Chair')

    def test_defaults(self):
        chair = self.env['salon.chair'].create({'date': self.at()})
        self.assertEqual(chair.chair_created_user, self.env.uid)
        self.assertEqual(chair.number_of_orders, 0)
        self.assertEqual(chair.collection_today, 0.0)
        self.assertFalse(chair.active_booking_chairs)

    def test_create_with_user_lines(self):
        """The last user line becomes the current user, earlier lines are
        closed with the start date of the next line."""
        user_a = self.env['res.users'].create(
            {'name': 'Stylist A', 'login': 'stylist_a'})
        user_b = self.env['res.users'].create(
            {'name': 'Stylist B', 'login': 'stylist_b'})
        start_a, start_b = self.at(), self.at(days=5)
        chair = self.env['salon.chair'].create({
            'date': self.at(),
            'user_line': [
                (0, 0, {'user_id': user_a.id, 'start_date': start_a}),
                (0, 0, {'user_id': user_b.id, 'start_date': start_b}),
            ],
        })
        self.assertEqual(chair.user_id, user_b)
        self.assertEqual(chair.date, start_b)
        line_a = chair.user_line.filtered(lambda line: line.user_id == user_a)
        line_b = chair.user_line.filtered(lambda line: line.user_id == user_b)
        self.assertEqual(line_a.end_date, start_b)
        self.assertFalse(line_b.end_date)
        self.assertTrue(user_b.user_salon_active)

    def test_user_line_deleted_with_chair(self):
        user = self.env['res.users'].create(
            {'name': 'Stylist', 'login': 'stylist_c'})
        chair = self.env['salon.chair'].create({
            'date': self.at(),
            'user_line': [(0, 0, {'user_id': user.id,
                                  'start_date': self.at()})]})
        line = chair.user_line
        chair.unlink()
        self.assertFalse(line.exists())

    def test_collection_today_updater(self):
        order = self.make_order()
        order.action_confirm()
        order.action_create_invoice()
        self.chair.collection_today = 0.0
        self.env['salon.chair'].collection_today_updater()
        self.assertEqual(self.chair.collection_today, 150.0)
        # a chair without invoiced orders stays at zero
        self.assertEqual(self.chair2.collection_today, 0.0)

    def test_collection_today_ignores_open_orders(self):
        order = self.make_order()
        order.action_confirm()
        self.env['salon.chair'].collection_today_updater()
        self.assertEqual(self.chair.collection_today, 0.0)
