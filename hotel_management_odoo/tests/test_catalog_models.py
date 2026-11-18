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
#############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import HotelCommon


@tagged('post_install', '-at_install')
class TestCatalogModels(HotelCommon):

    # ---- product.template (rooms) ----

    def test_room_capacity_constraint(self):
        with self.assertRaises(ValidationError):
            self.room1.num_person = 0
        with self.assertRaises(ValidationError):
            self._create_room('Bad', 10.0, persons=-1)

    def test_room_storable_constraint(self):
        with self.assertRaises(ValidationError):
            self.room1.write({'is_storable': True})

    def test_onchange_room_type(self):
        room = self.env['product.template'].new({'room_type': 'single'})
        room._onchange_room_type()
        self.assertEqual(room.num_person, 1)
        room.room_type = 'double'
        room._onchange_room_type()
        self.assertEqual(room.num_person, 2)
        room.room_type = 'dormitory'
        room._onchange_room_type()
        self.assertEqual(room.num_person, 4)

    # ---- simple catalog models ----

    def test_amenity(self):
        # 1x1 transparent PNG
        icon = ('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAHhZ0'
                'WwAAAABJRU5ErkJggg==')
        amenity = self.env['hotel.amenity'].create({
            'name': 'WiFi', 'icon': icon, 'description': '<p>Fast</p>'})
        self.room1.room_amenities_ids = [(4, amenity.id)]
        self.assertIn(amenity, self.room1.room_amenities_ids)

    def test_amenity_icon_optional(self):
        amenity = self.env['hotel.amenity'].create({'name': 'NoIcon'})
        self.assertFalse(amenity.icon)

    def test_account_move_extra_fields(self):
        booking = self._make_booking()
        move = self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': self.partner.id,
            'hotel_booking_id': booking.id})
        self.assertEqual(move.hotel_booking_id, booking)
        selection = dict(self.env['account.move.line']._fields['product_type'].selection)
        self.assertEqual(set(selection), {'room', 'food', 'event', 'service', 'fleet'})

    def test_teams(self):
        head = self._create_user('c_head', ['hotel_management_odoo.cleaning_team_group_head'])
        member = self._create_user('c_member', ['hotel_management_odoo.cleaning_team_group_user'])
        team = self.env['cleaning.team'].create({
            'name': 'Cleaners', 'team_head_id': head.id,
            'member_ids': [(6, 0, member.ids)]})
        self.assertEqual(team.member_ids, member)
        lead = self._create_user('m_lead', ['hotel_management_odoo.maintenance_team_group_leader'])
        mteam = self.env['maintenance.team'].create({
            'name': 'Fixers', 'user_id': lead.id, 'is_hotel': True})
        self.assertTrue(mteam.is_hotel)
