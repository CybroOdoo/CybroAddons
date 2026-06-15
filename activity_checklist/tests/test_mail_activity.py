# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.fields import Date


@tagged('post_install', '-at_install', 'activity_checklist')
class TestMailActivity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Find the activity.general model
        cls.general_model = cls.env['ir.model'].search([('model', '=', 'activity.general')], limit=1)
        # Create a test activity.general record
        cls.test_doc = cls.env['activity.general'].create({
            'name': 'Test Document'
        })
        # Create a mail.activity.type for test
        cls.activity_type = cls.env['mail.activity.type'].create({
            'name': 'Test Activity Type',
            'res_model': 'activity.general'
        })
        # Ensure target default record exists
        cls.general_activities_record = cls.env.ref('activity_checklist.general_activities', raise_if_not_found=False)
        if not cls.general_activities_record:
            cls.general_activities_record = cls.env['activity.general'].create({
                'name': 'General Activities Record'
            })

    def test_default_get(self):
        """Test default get behavior sets res_model_id to activity.general"""
        vals = self.env['mail.activity'].default_get(['res_model_id'])
        self.assertEqual(vals.get('res_model_id'), self.general_model.id)

    def test_get_date(self):
        """Test get_date calculations for different intervals"""
        base_date = Date.to_date('2026-06-12')
        activity = self.env['mail.activity'].create({
            'summary': 'Test Get Date',
            'res_model_id': self.general_model.id,
            'res_id': self.test_doc.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': base_date,
        })

        # Test Daily
        activity.interval = 'Daily'
        self.assertEqual(activity.get_date(), '2026-06-13')

        # Test Weekly
        activity.interval = 'Weekly'
        self.assertEqual(activity.get_date(), '2026-06-19')

        # Test Monthly
        activity.interval = 'Monthly'
        self.assertEqual(activity.get_date(), '2026-07-12')

        # Test Quarterly
        activity.interval = 'Quarterly'
        self.assertEqual(activity.get_date(), '2026-09-10')

        # Test Yearly
        activity.interval = 'Yearly'
        self.assertEqual(activity.get_date(), '2027-06-12')

    def test_onchange_new_date(self):
        """Test that _onchange_new_date computes and sets new_date if recurring is True"""
        base_date = Date.to_date('2026-06-12')
        activity = self.env['mail.activity'].new({
            'res_model_id': self.general_model.id,
            'res_id': self.test_doc.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': base_date,
            'recurring': True,
            'interval': 'Weekly'
        })
        activity._onchange_new_date()
        self.assertEqual(activity.new_date, Date.to_date('2026-06-19'))

        # If not recurring, new_date should be set to False
        activity.recurring = False
        activity._onchange_new_date()
        self.assertFalse(activity.new_date)

    def test_action_done_non_recurring(self):
        """Test action_done on a non-recurring activity"""
        activity = self.env['mail.activity'].create({
            'summary': 'Non Recurring Activity',
            'res_model_id': self.general_model.id,
            'res_id': self.test_doc.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': Date.today(),
            'recurring': False,
        })
        initial_activity_count = self.env['mail.activity'].with_context(active_test=False).search_count([])
        activity.action_done()

        # The activity should be archived/done (active=False or unlinked)
        self.assertFalse(activity.active)
        # Total count (including inactive) should be the same as no new activity is created
        self.assertEqual(self.env['mail.activity'].with_context(active_test=False).search_count([]), initial_activity_count)


    def test_action_done_recurring(self):
        """Test action_done on a recurring activity creates a new activity with next due date"""
        activity = self.env['mail.activity'].create({
            'summary': 'Recurring Activity',
            'res_model_id': self.general_model.id,
            'res_id': self.test_doc.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': Date.to_date('2026-06-12'),
            'recurring': True,
            'interval': 'Weekly',
            'new_date': Date.to_date('2026-06-19'),
        })

        activity.action_done()

        # Original activity is done/archived
        self.assertFalse(activity.active)

        # Find the newly created activity
        new_activity = self.env['mail.activity'].search([
            ('res_model_id', '=', self.general_model.id),
            ('res_id', '=', self.test_doc.id),
            ('active', '=', True),
            ('summary', '=', 'Recurring Activity')
        ])
        self.assertTrue(new_activity)
        self.assertEqual(new_activity.date_deadline, Date.to_date('2026-06-19'))
        self.assertEqual(new_activity.new_date, Date.to_date('2026-06-26'))
        self.assertTrue(new_activity.recurring)
        self.assertEqual(new_activity.interval, 'Weekly')

    def test_action_date_cron(self):
        """Test action_date automated/cron method creates recurring activities on deadline"""
        today = Date.today()
        activity = self.env['mail.activity'].create({
            'summary': 'Cron Recurring Activity',
            'res_model_id': self.general_model.id,
            'res_id': self.test_doc.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': today,
            'recurring': True,
            'interval': 'Daily',
            'new_date': today + timedelta(days=1),
        })

        # Run action_date
        self.env['mail.activity'].action_date()

        # Verify a new activity is created for tomorrow
        new_activity = self.env['mail.activity'].search([
            ('summary', '=', 'Cron Recurring Activity'),
            ('date_deadline', '=', today + timedelta(days=1))
        ])
        self.assertTrue(new_activity)
        self.assertEqual(new_activity.new_date, today + timedelta(days=2))

    def test_action_cancel(self):
        """Test action_cancel unlinks the activity and returns view action"""
        activity = self.env['mail.activity'].create({
            'summary': 'Activity to Cancel',
            'res_model_id': self.general_model.id,
            'res_id': self.test_doc.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': Date.today(),
        })
        activity_id = activity.id

        res = activity.action_cancel()

        # Verify it is unlinked/deleted
        remaining = self.env['mail.activity'].search([('id', '=', activity_id)])
        self.assertFalse(remaining)

        # Verify action result
        self.assertEqual(res.get('type'), 'ir.actions.act_window')
        self.assertEqual(res.get('res_model'), 'mail.activity')

    def test_action_open_origin(self):
        """Test action_open_origin returns the correct action dictionary"""
        activity = self.env['mail.activity'].create({
            'summary': 'Open Origin Activity',
            'res_model_id': self.general_model.id,
            'res_id': self.test_doc.id,
            'activity_type_id': self.activity_type.id,
            'date_deadline': Date.today(),
        })

        res = activity.action_open_origin()
        self.assertEqual(res.get('type'), 'ir.actions.act_window')
        self.assertEqual(res.get('res_model'), 'activity.general')
        self.assertEqual(res.get('res_id'), self.test_doc.id)
        self.assertEqual(res.get('view_mode'), 'form')
