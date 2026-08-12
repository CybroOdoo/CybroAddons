# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Aleena K(<https://www.cybrosys.com>)
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
from datetime import datetime, timedelta
from psycopg2.errors import NotNullViolation
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPersonalOrganiser(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.ref('base.user_admin')
        cls.calendar_event = cls.env['calendar.event'].create({
            'name': 'Demo Meeting',
            'start': datetime.now(),
            'stop': datetime.now() + timedelta(hours=1),
            'allday': True,
            'user_id': cls.user.id,
        })
        cls.task = cls.env['personal.organiser'].create({
            'task_title': 'Prepare Documentation',
            'date': datetime.now() + timedelta(days=1),
            'user_id': cls.user.id,
            'calendar_event_id': cls.calendar_event.id,
        })

    def test_task_creation(self):
        """Test task creation"""
        self.assertRecordValues(self.task, [{
            'task_title': 'Prepare Documentation',
            'user_id': self.user.id,
            'calendar_event_id': self.calendar_event.id,
        }])

    def test_calendar_event_relation(self):
        """Test calendar event relation"""
        self.assertEqual(
            self.task.calendar_event_id,
            self.calendar_event,
            "Calendar event relation failed"
        )

    def test_task_update(self):
        """Test task update"""
        self.task.write({
            'task_title': 'Updated Task'
        })
        self.assertRecordValues(self.task, [{
            'task_title': 'Updated Task',
        }])

    def test_required_task_title(self):
        """Test required title"""
        with self.assertRaises(NotNullViolation):
            self.env['personal.organiser'].create({
                'date': datetime.now(),
                'user_id': self.user.id,
            })

    def test_required_date(self):
        """Test required date"""
        with self.assertRaises(NotNullViolation):
            self.env['personal.organiser'].create({
                'task_title': 'Task Without Date',
                'user_id': self.user.id,
            })

    def test_task_deletion(self):
        """Test task deletion"""
        task = self.env['personal.organiser'].create({
            'task_title': 'Temporary Task',
            'date': datetime.now() + timedelta(days=1),
            'user_id': self.user.id,
        })
        task_id = task.id
        task.unlink()
        deleted_task = self.env['personal.organiser'].browse(
            task_id
        )
        self.assertFalse(
            deleted_task.exists(),
            "Task was not deleted properly"
        )

    def test_calendar_event_set_null_on_delete(self):
        """Test ondelete set null behavior"""
        task = self.env['personal.organiser'].create({
            'task_title': 'Calendar Task',
            'date': datetime.now() + timedelta(days=1),
            'user_id': self.user.id,
            'calendar_event_id': self.calendar_event.id,
        })
        self.calendar_event.unlink()
        self.assertFalse(
            task.calendar_event_id,
            "Calendar event was not set to null"
        )
