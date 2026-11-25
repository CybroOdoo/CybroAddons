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
class TestPetSettingScheduleWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Wizard Pet Owner',
            'phone': '+1234567890',
            'email': 'owner@example.com',
        })
        cls.sitter = cls.env['hr.employee'].create({
            'name': 'Caregiver Jamie',
            'is_walker_sitters': True,
        })
        cls.pet = cls.env['product.product'].create({
            'name': 'Rocky',
            'is_pet': True,
            'customer_id': cls.partner.id,
        })
        cls.service = cls.env['product.product'].create({
            'name': 'Overnight Stay',
            'is_pet_service': True,
            'list_price': 80.0,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

    def test_01_wizard_assign_sittings(self):
        """ Test wizard line transfer and persistent schedule creation """
        start_time = datetime.now() + timedelta(days=3)
        end_time = start_time + timedelta(hours=5)

        wizard = self.env['pet.sitting.schedule'].create({
            'walker_sitting_id': self.sitter.id,
            'schedule_description': 'Care for Rocky',
            'reference_id': self.sale_order.id,
            'date_start': start_time,
            'end_date': end_time,
            'pet_info_ids': [Command.create({
                'num': self.pet.id,
                'customer': self.partner.id,
            })],
            'service_ids': [Command.create({
                'name': self.service.id,
            })],
            'attendees_ids': [Command.create({
                'attendees_id': self.partner.id,
            })],
        })

        # Verify wizard lines and related values
        self.assertEqual(wizard.attendees_ids.phone, '+1234567890')
        self.assertEqual(wizard.attendees_ids.email, 'owner@example.com')
        self.assertEqual(wizard.pet_info_ids.name, 'Rocky')
        self.assertEqual(wizard.service_ids.sale_price, 80.0)

        # Execute assignment
        action = wizard.assign_sittings()
        self.assertEqual(action.get('res_model'), 'sitting.schedule')
        self.assertEqual(action.get('view_mode'), 'form')

        schedule_id = action.get('res_id')
        schedule = self.env['sitting.schedule'].browse(schedule_id)
        self.assertTrue(schedule.exists())
        self.assertEqual(schedule.name, 'Care for Rocky')
        self.assertEqual(schedule.number_id, self.sale_order)
        self.assertEqual(schedule.date_start, start_time)
        self.assertEqual(schedule.end_date, end_time)
        self.assertEqual(len(schedule.pet_info_ids), 1)
        self.assertEqual(schedule.pet_info_ids.num, self.pet)
        self.assertEqual(len(schedule.service_ids), 1)
        self.assertEqual(schedule.service_ids.name, self.service)
        self.assertIn(self.sitter, schedule.attendees_ids)
