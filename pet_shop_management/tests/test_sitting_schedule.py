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
from datetime import datetime, timedelta
from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'pet_shop_management')
class TestSittingSchedule(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Schedule Customer',
        })
        cls.pet_type = cls.env['pet.type'].create({
            'name': 'Poodle',
        })
        cls.pet = cls.env['product.product'].create({
            'name': 'Max',
            'is_pet': True,
            'color': 'White',
            'stay': 'Cage 1',
            'sex': 'male',
            'pet_type_id': cls.pet_type.id,
            'customer_id': cls.partner.id,
        })
        cls.service = cls.env['product.product'].create({
            'name': 'Daily Walking',
            'is_pet_service': True,
            'standard_price': 15.0,
            'list_price': 25.0,
        })
        cls.sitter = cls.env['hr.employee'].create({
            'name': 'Alex Sitter',
            'is_walker_sitters': True,
        })

    def test_01_sitting_schedule_creation_and_relations(self):
        """ Test creating sitting schedule with pet info and services """
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=3)

        schedule = self.env['sitting.schedule'].create({
            'name': 'Weekend Sitting',
            'date_start': start_time,
            'end_date': end_time,
            'attendees_ids': [Command.set([self.sitter.id])],
            'pet_info_ids': [Command.create({
                'num': self.pet.id,
                'customer': self.partner.id,
            })],
            'service_ids': [Command.create({
                'name': self.service.id,
            })],
        })

        self.assertTrue(schedule.exists())
        self.assertEqual(len(schedule.attendees_ids), 1)
        self.assertEqual(schedule.attendees_ids[0], self.sitter)

        # Check pet.info line and related fields
        self.assertEqual(len(schedule.pet_info_ids), 1)
        pet_line = schedule.pet_info_ids[0]
        self.assertEqual(pet_line.num, self.pet)
        self.assertEqual(pet_line.name, 'Max')
        self.assertEqual(pet_line.color, 'White')
        self.assertEqual(pet_line.stay, 'Cage 1')
        self.assertEqual(pet_line.sex, 'male')
        self.assertEqual(pet_line.pet_type_id, self.pet_type)
        self.assertEqual(pet_line.customer, self.partner)

        # Check pet.service line and related prices
        self.assertEqual(len(schedule.service_ids), 1)
        service_line = schedule.service_ids[0]
        self.assertEqual(service_line.name, self.service)
        self.assertEqual(service_line.cost, 15.0)
        self.assertEqual(service_line.sale_price, 25.0)
