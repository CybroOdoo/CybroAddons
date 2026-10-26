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
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMailActivityChecklist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.activity_model = cls.env['ir.model'].search(
            [('model', '=', 'activity.general')], limit=1
        )
        cls.general_activity = cls.env.ref(
            'activity_checklist.general_activities', raise_if_not_found=False
        )
        if not cls.general_activity:
            cls.general_activity = cls.env['activity.general'].create({
                'name': 'Test General Activity',
            })
        cls.activity_type = cls.env['mail.activity.type'].search([], limit=1)

    def test_01_default_get_general_activity(self):
        """Test default model and document ID resolution."""
        defaults = self.env['mail.activity'].default_get(['res_model_id', 'res_id'])
        self.assertEqual(defaults.get('res_model_id'), self.activity_model.id)
        if self.general_activity:
            self.assertEqual(defaults.get('res_id'), self.general_activity.id)
            self.assertIsInstance(defaults.get('res_id'), int)

    def test_02_get_date_relativedelta_intervals(self):
        """Test date calculations for all recurring intervals using relativedelta."""
        base = date(2026, 1, 31)
        activity = self.env['mail.activity'].create({
            'summary': 'Test Recurrence Intervals',
            'res_model_id': self.activity_model.id,
            'res_id': self.general_activity.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': base,
            'recurring': True,
            'interval': 'Daily',
        })

        # Daily
        self.assertEqual(activity.get_date(), date(2026, 2, 1))

        # Weekly
        activity.interval = 'Weekly'
        self.assertEqual(activity.get_date(), date(2026, 2, 7))

        # Monthly (boundary case: Jan 31 -> Feb 28)
        activity.interval = 'Monthly'
        self.assertEqual(activity.get_date(), date(2026, 2, 28))

        # Quarterly (boundary case: Jan 31 -> Apr 30)
        activity.interval = 'Quarterly'
        self.assertEqual(activity.get_date(), date(2026, 4, 30))

        # Yearly (boundary case: Feb 29 leap year -> Feb 28 next year)
        leap_base = date(2024, 2, 29)
        activity.date_deadline = leap_base
        activity.interval = 'Yearly'
        self.assertEqual(activity.get_date(), date(2025, 2, 28))

    def test_03_onchange_new_date(self):
        """Test onchange updates next due date."""
        base = date(2026, 5, 10)
        activity = self.env['mail.activity'].new({
            'res_model_id': self.activity_model.id,
            'res_id': self.general_activity.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': base,
            'recurring': True,
            'interval': 'Monthly',
        })
        activity._onchange_new_date()
        self.assertEqual(activity.new_date, date(2026, 6, 10))

    def test_04_action_done_recurring_activity(self):
        """Test Mark As Done creates the next occurrence for recurring activities."""
        base_deadline = date(2026, 6, 1)
        activity = self.env['mail.activity'].create({
            'summary': 'Recurring Task',
            'res_model_id': self.activity_model.id,
            'res_id': self.general_activity.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': base_deadline,
            'priority': '2',
            'recurring': True,
            'interval': 'Monthly',
            'new_date': date(2026, 7, 1),
        })

        activity.action_done()

        # Verify next activity created with correct next due date and recurring settings
        next_activity = self.env['mail.activity'].search([
            ('res_model_id', '=', self.activity_model.id),
            ('res_id', '=', self.general_activity.id),
            ('summary', '=', 'Recurring Task'),
            ('recurring', '=', True),
        ])
        self.assertTrue(next_activity.exists())
        self.assertEqual(next_activity.date_deadline, date(2026, 7, 1))
        self.assertEqual(next_activity.new_date, date(2026, 8, 1))
        self.assertEqual(next_activity.priority, '2')
        self.assertEqual(next_activity.interval, 'Monthly')

    def test_05_action_done_non_recurring_activity(self):
        """Test Mark As Done for non-recurring activities does not create a next activity."""
        activity = self.env['mail.activity'].create({
            'summary': 'One-off Task',
            'res_model_id': self.activity_model.id,
            'res_id': self.general_activity.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': fields.Date.today(),
            'recurring': False,
        })
        activity_id = activity.id
        activity.action_done()

        self.assertFalse(self.env['mail.activity'].search([('id', '=', activity_id)]).exists())
        next_activity = self.env['mail.activity'].search([
            ('summary', '=', 'One-off Task'),
        ])
        self.assertFalse(next_activity.exists())

    def test_06_action_date_cron(self):
        """Test automated action_date cron triggers recurrence for due activities."""
        today = fields.Date.today()
        activity = self.env['mail.activity'].create({
            'summary': 'Cron Due Task Recurrence Unique',
            'res_model_id': self.activity_model.id,
            'res_id': self.general_activity.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': today,
            'recurring': True,
            'interval': 'Weekly',
        })
        activity_id = activity.id

        self.env['mail.activity'].action_date()

        # The original due activity is completed/unlinked
        self.assertFalse(self.env['mail.activity'].search([('id', '=', activity_id)]).exists())

        # Exactly one new activity is created for the next occurrence
        next_activity = self.env['mail.activity'].search([
            ('summary', '=', 'Cron Due Task Recurrence Unique'),
            ('recurring', '=', True),
        ])
        self.assertEqual(len(next_activity), 1)
        self.assertEqual(next_activity.date_deadline, today + relativedelta(weeks=1))

    def test_07_action_cancel(self):
        """Test action_cancel unlinks activity."""
        activity = self.env['mail.activity'].create({
            'summary': 'Cancel Task',
            'res_model_id': self.activity_model.id,
            'res_id': self.general_activity.id,
            'activity_type_id': self.activity_type.id,
        })
        activity_id = activity.id
        res = activity.action_cancel()
        self.assertEqual(res.get('res_model'), 'mail.activity')
        self.assertFalse(self.env['mail.activity'].search([('id', '=', activity_id)]).exists())

    def test_08_action_open_origin(self):
        """Test action_open_origin returns form action for related document."""
        activity = self.env['mail.activity'].create({
            'summary': 'Origin Task',
            'res_model_id': self.activity_model.id,
            'res_id': self.general_activity.id,
            'activity_type_id': self.activity_type.id,
        })
        action = activity.action_open_origin()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'activity.general')
        self.assertEqual(action.get('res_id'), self.general_activity.id)

    def test_09_action_done_recurring_without_new_date(self):
        """Test Mark As Done for recurring activity without precomputed new_date."""
        base_deadline = date(2026, 9, 15)
        activity = self.env['mail.activity'].create({
            'summary': 'Recurring Without New Date',
            'res_model_id': self.activity_model.id,
            'res_id': self.general_activity.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': base_deadline,
            'recurring': True,
            'interval': 'Daily',
            'new_date': False,
        })
        activity.action_done()

        next_activity = self.env['mail.activity'].search([
            ('summary', '=', 'Recurring Without New Date'),
        ])
        self.assertTrue(next_activity.exists())
        self.assertIsNotNone(next_activity.date_deadline)
        self.assertNotEqual(next_activity.date_deadline, False)
        self.assertEqual(next_activity.date_deadline, date(2026, 9, 16))

    def test_10_dynamic_state_computation(self):
        """Test that state is dynamically computed based on today's date."""
        today = fields.Date.today()
        act_today = self.env['mail.activity'].create({
            'summary': 'Due Today',
            'res_model_id': self.activity_model.id,
            'res_id': self.general_activity.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': today,
        })
        act_overdue = self.env['mail.activity'].create({
            'summary': 'Overdue',
            'res_model_id': self.activity_model.id,
            'res_id': self.general_activity.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': today - relativedelta(days=2),
        })
        act_planned = self.env['mail.activity'].create({
            'summary': 'Planned',
            'res_model_id': self.activity_model.id,
            'res_id': self.general_activity.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': today + relativedelta(days=2),
        })
        self.assertEqual(act_today.state, 'today')
        self.assertEqual(act_overdue.state, 'overdue')
        self.assertEqual(act_planned.state, 'planned')
