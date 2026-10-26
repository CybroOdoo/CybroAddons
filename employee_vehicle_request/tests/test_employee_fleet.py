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
from datetime import timedelta
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo import Command, fields


@tagged('post_install', '-at_install')
class TestEmployeeFleetRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_employee = cls.env['res.users'].create({
            'name': 'Regular Employee User',
            'login': 'regular_employee_user',
            'email': 'regular_employee@example.com',
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })
        cls.user_hr = cls.env['res.users'].create({
            'name': 'HR Officer User',
            'login': 'hr_officer_user',
            'email': 'hr_officer@example.com',
            'group_ids': [Command.set([
                cls.env.ref('base.group_user').id,
                cls.env.ref('hr.group_hr_user').id,
            ])],
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Vehicle Request Employee',
            'work_email': 'vehicle.request@example.com',
            'user_id': cls.user_employee.id,
        })
        brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Vehicle Brand',
        })
        model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Vehicle Model',
            'brand_id': brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': 'TEST-VEHICLE',
        })

    def _dates(self, start_days=1, end_days=2):
        start = fields.Datetime.now() + timedelta(days=start_days)
        end = fields.Datetime.now() + timedelta(days=end_days)
        return start, end

    def _create_request(self, start_days=1, end_days=2, **values):
        date_from, date_to = self._dates(start_days, end_days)
        request_values = {
            'employee_id': self.employee.id,
            'fleet_id': self.vehicle.id,
            'date_from': date_from,
            'date_to': date_to,
            'purpose': 'Business travel',
        }
        request_values.update(values)
        return self.env['employee.fleet'].create(request_values)

    def test_request_creation_assigns_sequence_and_default_state(self):
        request = self._create_request()

        self.assertTrue(request.name)
        self.assertTrue(request.name.startswith('VR'))
        self.assertEqual(request.state, 'draft')
        self.assertEqual(request.employee_id, self.employee)
        self.assertEqual(request.fleet_id, self.vehicle)

    def test_send_request_creates_reservation_and_waits_for_approval(self):
        request = self._create_request()

        request.action_send()

        self.assertEqual(request.state, 'waiting')
        self.assertTrue(request.reserved_fleet_id)
        self.assertEqual(request.reserved_fleet_id.reserved_obj_id, self.vehicle)
        self.assertEqual(request.reserved_fleet_id.employee_id, self.employee)
        self.assertEqual(request.reserved_fleet_id.date_from, request.date_from)
        self.assertEqual(request.reserved_fleet_id.date_to, request.date_to)

    def test_send_overlapping_request_raises_and_does_not_reserve(self):
        first_request = self._create_request(start_days=3, end_days=5)
        first_request.action_send()
        overlapping_request = self._create_request(start_days=4, end_days=6)

        with self.assertRaises(UserError):
            overlapping_request.action_send()

        self.assertEqual(overlapping_request.state, 'draft')
        self.assertFalse(overlapping_request.reserved_fleet_id)

    def test_request_rejects_end_date_before_start_date(self):
        date_from, date_to = self._dates(start_days=3, end_days=2)

        with self.assertRaises(ValidationError):
            self._create_request(date_from=date_from, date_to=date_to)

    def test_approve_request_updates_state(self):
        request = self._create_request()
        request.action_send()

        with patch('odoo.addons.mail.models.mail_mail.MailMail.send'):
            request.action_approve()

        self.assertEqual(request.state, 'confirm')
        self.assertTrue(request.reserved_fleet_id)

    def test_reject_request_removes_reservation_and_releases_vehicle(self):
        request = self._create_request()
        request.action_send()
        reservation = request.reserved_fleet_id

        with patch('odoo.addons.mail.models.mail_mail.MailMail.send'):
            request.action_reject()

        self.assertEqual(request.state, 'reject')
        self.assertFalse(request.reserved_fleet_id)
        self.assertFalse(reservation.exists())

    def test_cancel_request_removes_reservation_and_releases_vehicle(self):
        request = self._create_request()
        request.action_send()
        reservation = request.reserved_fleet_id

        request.action_cancel()

        self.assertEqual(request.state, 'cancel')
        self.assertFalse(request.reserved_fleet_id)
        self.assertFalse(reservation.exists())

    def test_return_request_records_return_time_and_releases_vehicle(self):
        request = self._create_request()
        request.action_send()
        with patch('odoo.addons.mail.models.mail_mail.MailMail.send'):
            request.action_approve()
        reservation = request.reserved_fleet_id

        request.action_return()

        self.assertEqual(request.state, 'return')
        self.assertTrue(request.returned_date)
        self.assertFalse(request.reserved_fleet_id)
        self.assertFalse(reservation.exists())

    def test_multi_record_actions(self):
        req1 = self._create_request(start_days=1, end_days=2)
        req2 = self._create_request(start_days=3, end_days=4)
        records = req1 | req2

        # action_send on multi records
        records.action_send()
        self.assertEqual(req1.state, 'waiting')
        self.assertEqual(req2.state, 'waiting')

        # action_cancel on multi records
        records.action_cancel()
        self.assertEqual(req1.state, 'cancel')
        self.assertEqual(req2.state, 'cancel')
        self.assertFalse(req1.reserved_fleet_id)
        self.assertFalse(req2.reserved_fleet_id)

    def test_available_fleet_ids_computation_and_onchange_reset(self):
        request = self._create_request(start_days=5, end_days=6)
        request.action_send()

        new_request = self.env['employee.fleet'].new({
            'date_from': request.date_from,
            'date_to': request.date_to,
            'fleet_id': self.vehicle.id,
        })
        # Ensure the reserved vehicle is excluded from computed available vehicles
        self.assertNotIn(self.vehicle, new_request.available_fleet_ids)

        # Calling onchange resets fleet_id because it is no longer available
        new_request._onchange_date_from()
        self.assertFalse(new_request.fleet_id)

    def test_unauthorized_user_cannot_approve(self):
        request = self._create_request()
        request.action_send()
        with self.assertRaises(AccessError):
            request.with_user(self.user_employee).action_approve()

    def test_unauthorized_user_cannot_reject(self):
        request = self._create_request()
        request.action_send()
        with self.assertRaises(AccessError):
            request.with_user(self.user_employee).action_reject()

    def test_unauthorized_user_cannot_return(self):
        request = self._create_request()
        request.action_send()
        with patch('odoo.addons.mail.models.mail_mail.MailMail.send'):
            request.action_approve()
        with self.assertRaises(AccessError):
            request.with_user(self.user_employee).action_return()

    def test_hr_user_can_approve_and_return(self):
        request = self._create_request()
        request.action_send()
        with patch('odoo.addons.mail.models.mail_mail.MailMail.send'):
            request.with_user(self.user_hr).action_approve()
        self.assertEqual(request.state, 'confirm')

        request.with_user(self.user_hr).action_return()
        self.assertEqual(request.state, 'return')

    def test_employee_cannot_delete_other_reservation(self):
        request = self._create_request()
        request.action_send()
        reservation = request.reserved_fleet_id
        other_user = self.env['res.users'].create({
            'name': 'Other Employee User',
            'login': 'other_employee_user_res',
            'email': 'other_res@example.com',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        with self.assertRaises(AccessError):
            reservation.with_user(other_user).unlink()

    def test_employee_cannot_delete_other_vehicle_request(self):
        request = self._create_request()
        other_user = self.env['res.users'].create({
            'name': 'Other Employee User 2',
            'login': 'other_employee_user_req',
            'email': 'other_req@example.com',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        with self.assertRaises(AccessError):
            request.with_user(other_user).unlink()

    def test_employee_cannot_read_other_reservation(self):
        request = self._create_request()
        request.action_send()
        reservation = request.reserved_fleet_id
        other_user = self.env['res.users'].create({
            'name': 'Other Employee User 3',
            'login': 'other_employee_user_read',
            'email': 'other_read@example.com',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        # Searching reservations with other_user should not include this reservation
        found_reservations = self.env['fleet.reserved'].with_user(other_user).search([
            ('id', '=', reservation.id)
        ])
        self.assertNotIn(reservation, found_reservations)
