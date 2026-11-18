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
class TestCleaningRequest(HotelCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.head = cls._create_user(
            'clean_head', ['hotel_management_odoo.cleaning_team_group_head'])
        cls.member = cls._create_user(
            'clean_member', ['hotel_management_odoo.cleaning_team_group_user'])
        cls.team = cls.env['cleaning.team'].create({
            'name': 'Team A', 'team_head_id': cls.head.id,
            'member_ids': [(6, 0, cls.member.ids)]})

    def _request(self, **vals):
        base = {'cleaning_type': 'room', 'team_id': self.team.id,
                'room_id': self.room1.id}
        base.update(vals)
        return self.env['cleaning.request'].create(base)

    def test_assign_validations(self):
        req = self._request()
        with self.assertRaises(ValidationError):
            req.action_assign_cleaning()  # no assignee
        req.assigned_id = self.member
        req.room_id = False
        with self.assertRaises(ValidationError):
            req.action_assign_cleaning()
        hotel = self._request(cleaning_type='hotel', room_id=False,
                              assigned_id=self.member.id)
        with self.assertRaises(ValidationError):
            hotel.action_assign_cleaning()
        vehicle = self._request(cleaning_type='vehicle', room_id=False,
                                assigned_id=self.member.id)
        with self.assertRaises(ValidationError):
            vehicle.action_assign_cleaning()

    def test_full_workflow(self):
        req = self._request(assigned_id=self.member.id)
        req.action_assign_cleaning()
        self.assertEqual(req.state, 'assign')
        req.action_start_cleaning()
        self.assertEqual(req.state, 'ongoing')
        with self.assertRaises(ValidationError):
            req.action_assign_support()
        req.support_reason = 'Need hands'
        req.action_assign_support()
        self.assertEqual(req.state, 'support')
        with self.assertRaises(ValidationError):
            req.action_assign_assign_support()
        req.support_team_ids = self.member
        req.action_assign_assign_support()
        self.assertEqual(req.state, 'ongoing')
        req.action_done_cleaning()
        self.assertEqual(req.state, 'done')

    def test_maintain_request_for_each_type(self):
        room_req = self._request()
        res = room_req.action_maintain_request()
        self.assertEqual(res['params']['type'], 'success')
        mr = self.env['maintenance.request'].search([
            ('name', '=', 'Maintenance Request - %s' % room_req.sequence)])
        self.assertEqual(mr.room_maintenance_ids, self.room1)
        vehicle = self._make_vehicle('Cleaned car')
        veh_req = self._request(cleaning_type='vehicle', room_id=False,
                                vehicle_id=vehicle.id)
        veh_req.action_maintain_request()
        mr = self.env['maintenance.request'].search([
            ('name', '=', 'Maintenance Request - %s' % veh_req.sequence)])
        self.assertEqual(mr.vehicle_maintenance_id, vehicle)
        hotel_req = self._request(cleaning_type='hotel', room_id=False, hotel='Pool')
        hotel_req.action_maintain_request()
        mr = self.env['maintenance.request'].search([
            ('name', '=', 'Maintenance Request - %s' % hotel_req.sequence)])
        self.assertEqual(mr.hotel_maintenance, 'Pool')
