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
class TestMaintenance(HotelCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leader = cls._create_user(
            'm_leader', ['hotel_management_odoo.maintenance_team_group_leader'])
        cls.worker = cls._create_user(
            'm_worker', ['hotel_management_odoo.maintenance_team_group_user'])
        cls.team = cls.env['maintenance.team'].create({
            'name': 'Hotel Fixers', 'is_hotel': True, 'user_id': cls.leader.id,
            'member_ids': [(6, 0, cls.worker.ids)]})

    def _request(self, **vals):
        base = {'name': 'Fix', 'type': 'room', 'is_hotel': True,
                'room_maintenance_ids': [(6, 0, self.room1.ids)]}
        base.update(vals)
        return self.env['maintenance.request'].create(base)

    def test_assign_team_validations(self):
        with self.assertRaises(ValidationError):
            self._request(room_maintenance_ids=False).action_assign_team()
        with self.assertRaises(ValidationError):
            self._request(type='vehicle').action_assign_team()
        with self.assertRaises(ValidationError):
            self._request(type='hotel').action_assign_team()
        with self.assertRaises(ValidationError):
            self._request(type='cleaning').action_assign_team()
        with self.assertRaises(ValidationError):
            self._request().action_assign_team()  # no team

    def test_full_workflow(self):
        req = self._request(team_id=self.team.id)
        req.action_assign_team()
        self.assertEqual(req.state, 'team_leader_approve')
        with self.assertRaises(ValidationError):
            req.action_assign_user()
        req.assigned_user_id = self.worker
        req.action_assign_user()
        self.assertEqual(req.state, 'pending')
        req.action_start()
        self.assertEqual(req.state, 'ongoing')
        with self.assertRaises(ValidationError):
            req.action_support()
        req.support_reason = 'Need ladder'
        req.action_support()
        self.assertEqual(req.state, 'support')
        with self.assertRaises(ValidationError):
            req.action_assign_support()
        req.support_team_ids = self.worker
        req.action_assign_support()
        self.assertEqual(req.state, 'ongoing')
        with self.assertRaises(ValidationError):
            req.action_complete()
        req.remarks = 'All good'
        req.action_complete()
        self.assertEqual(req.state, 'verify')
        req.action_verify()
        self.assertEqual(req.state, 'done')
