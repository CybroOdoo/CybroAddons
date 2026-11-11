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
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from .common import SalonCommon


@tagged('post_install', '-at_install')
class TestSalonSecurity(SalonCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.salon_user = new_test_user(
            cls.env, login='salon_chair_user',
            groups='salon_management.group_salon_user')
        cls.salon_manager = new_test_user(
            cls.env, login='salon_manager_user',
            groups='salon_management.group_salon_manager')

    def test_user_can_read_and_create_orders(self):
        order = self.make_order().with_user(self.salon_user)
        self.assertEqual(order.customer_name, 'Walk-in')
        created = self.env['salon.order'].with_user(self.salon_user).create({
            'customer_name': 'By user', 'chair_id': self.chair2.id,
            'start_time': self.at(days=4),
            'order_line_ids': [(0, 0, {
                'service_id': self.service_hair.id, 'price': 100.0,
                'price_subtotal': 100.0, 'time_taken': 1.0})]})
        self.assertTrue(created.id)

    def test_user_cannot_delete_order(self):
        order = self.make_order().with_user(self.salon_user)
        with self.assertRaises(AccessError):
            order.unlink()

    def test_manager_can_delete_order(self):
        order = self.make_order().with_user(self.salon_manager)
        order.unlink()
        self.assertFalse(order.exists())

    def test_user_cannot_create_chair_or_service(self):
        with self.assertRaises(AccessError):
            self.env['salon.chair'].with_user(self.salon_user).create(
                {'date': self.at()})
        with self.assertRaises(AccessError):
            self.env['salon.service'].with_user(self.salon_user).create(
                {'name': 'X', 'price': 1})

    def test_manager_can_manage_master_data(self):
        chair = self.env['salon.chair'].with_user(self.salon_manager).create(
            {'date': self.at()})
        service = self.env['salon.service'].with_user(
            self.salon_manager).create({'name': 'Y', 'price': 1})
        holiday = self.env['salon.holiday'].with_user(
            self.salon_manager).create({'name': 'Holiday'})
        hours = self.env['salon.working.hours'].with_user(
            self.salon_manager).create({'name': 'Hours'})
        self.assertTrue(chair and service and holiday and hours)

    def test_user_can_access_bookings(self):
        booking = self.make_booking()
        found = self.env['salon.booking'].with_user(self.salon_user).search(
            [('id', '=', booking.id)])
        self.assertEqual(found, booking)

    def test_manager_can_access_bookings(self):
        booking = self.make_booking().with_user(self.salon_manager)
        self.assertEqual(booking.state, 'draft')

    def test_public_cannot_access_orders(self):
        public = self.env.ref('base.public_user')
        order = self.make_order().with_user(public)
        for action in (lambda: order.read(['customer_name']),
                       lambda: order.write({'note': 'hack'}),
                       order.unlink):
            with self.assertRaises(AccessError):
                action()
        with self.assertRaises(AccessError):
            self.env['salon.chair.user'].with_user(public).search([])
        with self.assertRaises(AccessError):
            self.env['salon.order.line'].with_user(public).search([])
        for model in ('salon.chair', 'salon.stage',
                      'salon.working.hours', 'salon.holiday', 'salon.booking'):
            with self.assertRaises(AccessError, msg=model):
                self.env[model].with_user(public).search([])

    def test_public_can_read_services(self):
        """Services (public price list) stay readable: saving the booking's
        many2many ``service_ids`` requires read access on them."""
        public = self.env.ref('base.public_user')
        self.assertTrue(
            self.env['salon.service'].with_user(public).search([]))

    def test_public_booking_with_services(self):
        """Public visitors can book services."""
        public = self.env.ref('base.public_user')
        booking = self.env['salon.booking'].with_user(public).create({
            'name': 'Public', 'chair_id': self.chair.id,
            'time': self.at(days=7),
            'service_ids': [(6, 0, self.service_hair.ids)]})
        self.assertTrue(booking.id)

    def test_public_can_create_booking(self):
        public = self.env.ref('base.public_user')
        booking = self.env['salon.booking'].with_user(public).create({
                'name': 'Public', 'chair_id': self.chair.id,
                'time': self.at(days=6)})
        self.assertTrue(booking.id)
