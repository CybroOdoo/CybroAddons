# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import timedelta
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.user
        cls.activity_type = cls.env['mail.activity.type'].search(
            [],
            limit=1
        )
        cls.partner = cls.env['res.partner'].create({
            'name': 'Demo Partner',
        })
        cls.model_id = cls.env['ir.model']._get_id(
            'res.partner'
        )

    def _create_activity(self, state, summary):
        """Helper method to create activities."""
        deadline = fields.Date.today()
        if state == 'planned':
            deadline = fields.Date.today() + timedelta(days=2)
        elif state == 'overdue':
            deadline = fields.Date.today() - timedelta(days=2)
        activity = self.env['mail.activity'].create({
            'summary': summary,
            'activity_type_id': self.activity_type.id,
            'res_model_id': self.model_id,
            'res_id': self.partner.id,
            'user_id': self.user.id,
            'date_deadline': deadline,
        })
        if state == 'done':
            activity.action_done()
        elif state == 'cancel':
            activity.action_cancel()
        return activity

    def test_get_activity_groups_excludes_done_cancel(self):
        """Test done and cancelled activities are excluded."""
        self._create_activity(
            'today',
            'Today Activity'
        )
        self._create_activity(
            'planned',
            'Planned Activity'
        )
        self._create_activity(
            'done',
            'Done Activity'
        )
        self._create_activity(
            'cancel',
            'Cancelled Activity'
        )
        result = self.env.user._get_activity_groups()
        activity_data = False
        for rec in result:
            if rec['model'] == 'res.partner':
                activity_data = rec
                break
        self.assertTrue(activity_data)
        self.assertEqual(
            activity_data['today_count'],
            1
        )
        self.assertEqual(
            activity_data['planned_count'],
            1
        )
        self.assertEqual(
            activity_data['total_count'],
            1
        )

    def test_done_activity_not_included(self):
        """Test done activity excluded from systray."""
        done_activity = self._create_activity(
            'done',
            'Completed Activity'
        )
        result = self.env.user._get_activity_groups()
        found = False
        for rec in result:
            if 'activity_ids' in rec:
                if done_activity.id in rec['activity_ids']:
                    found = True
        self.assertFalse(found)

    def test_cancel_activity_not_included(self):
        """Test cancelled activity excluded from systray."""
        cancel_activity = self._create_activity(
            'cancel',
            'Cancelled Activity'
        )
        result = self.env.user._get_activity_groups()
        found = False
        for rec in result:
            if 'activity_ids' in rec:
                if cancel_activity.id in rec['activity_ids']:
                    found = True
        self.assertFalse(found)
