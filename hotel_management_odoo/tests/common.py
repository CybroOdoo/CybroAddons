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
"""Shared fixtures for the hotel_management_odoo test-suite."""
from datetime import timedelta

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class HotelCommon(TransactionCase):
    """Base class creating the master data used by most tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env['res.partner'].create({'name': 'Test Guest'})
        cls.user_admin = cls._create_user(
            'hotel_admin', ['hotel_management_odoo.hotel_group_admin'])
        cls.floor = cls.env['hotel.floor'].create({
            'name': 'Ground', 'user_id': cls.user_admin.id})
        cls.room1 = cls._create_room('Room 101', 100.0)
        cls.room2 = cls._create_room('Room 102', 150.0)
        cls.service = cls.env['hotel.service'].create({
            'name': 'Laundry', 'unit_price': 10.0, 'taxes_ids': False})

    # ------------------------------------------------------------------
    @classmethod
    def _create_user(cls, login, group_xmlids):
        groups = [cls.env.ref('base.group_user').id]
        groups += [cls.env.ref(x).id for x in group_xmlids]
        return cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': login.title(),
            'login': login,
            'email': '%s@example.com' % login,
            'group_ids': [Command.set(groups)],
        })

    @classmethod
    def _create_room(cls, name, price, room_type='single', persons=1):
        return cls.env['product.template'].create({
            'name': name,
            'is_room': True,
            'type': 'consu',
            'list_price': price,
            'taxes_id': [Command.clear()],
            'room_type': room_type,
            'num_person': persons,
            'floor_id': cls.floor.id,
        })

    @classmethod
    def _make_booking(cls, rooms=None, days=2, **extra):
        """Create a booking with one line per room (price set explicitly)."""
        rooms = rooms if rooms is not None else cls.room1
        start = fields.Datetime.now()
        end = start + timedelta(days=days)
        lines = [Command.create({
            'room_id': room.id,
            'checkin_date': start,
            'checkout_date': end,
            'uom_qty': days,
            'price_unit': room.list_price,
        }) for room in rooms]
        vals = {
            'partner_id': cls.partner.id,
            'room_line_ids': lines,
        }
        vals.update(extra)
        return cls.env['room.booking'].create(vals)

    @classmethod
    def _make_vehicle(cls, name='Hotel Car', price=2.0):
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Brand ' + name})
        return cls.env['fleet.vehicle.model'].create({
            'name': name, 'brand_id': brand.id, 'price_per_km': price})

    @classmethod
    def _make_food(cls, name='Pizza', price=8.0):
        category = cls.env['lunch.product.category'].create({'name': 'Cat ' + name})
        supplier = cls.env['lunch.supplier'].create({
            'partner_id': cls.env['res.partner'].create({'name': 'Sup ' + name}).id})
        return cls.env['lunch.product'].create({
            'name': name, 'price': price,
            'category_id': category.id, 'supplier_id': supplier.id})
