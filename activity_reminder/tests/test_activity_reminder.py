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
from odoo.tests import common, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestActivityReminder(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a test user to receive the reminder
        cls.test_user = cls.env['res.users'].create({
            'name': 'Activity Test User',
            'login': 'activity_test_user',
            'email': 'recipient@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

        # Ensure the current user has a valid email to avoid validation or parsing issues
        cls.env.user.email = 'sender@example.com'

    def test_activity_cron_reminder_email(self):
        """Test that the activity_cron cron job finds due activities and sends reminder emails."""
        # Clean/count existing mail messages/mails with this subject to ensure clear assertion
        initial_mail_count = self.env['mail.mail'].search_count([
            ('subject', 'like', 'Reminder: Activity Test Activity is due')
        ])

        # Create a mail.activity record with reminder_due_date = today
        activity = self.env['mail.activity'].create({
            'summary': 'Test Activity',
            'reminder_due_date': fields.Date.today(),
            'date_deadline': fields.Date.today(),
            'user_id': self.test_user.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': self.test_user.partner_id.id,
        })

        # Run the cron function on persistent mail.activity model
        self.env['mail.activity'].activity_cron()

        # Check if the mail was created
        sent_mails = self.env['mail.mail'].search([
            ('subject', 'like', 'Reminder: Activity Test Activity is due')
        ])

        self.assertEqual(len(sent_mails), initial_mail_count + 1, "Exactly one reminder email should be created and sent")
        latest_mail = sent_mails[0]
        self.assertEqual(latest_mail.email_to, self.test_user.email)
        self.assertEqual(latest_mail.email_from, self.env.user.email)

    def test_wizard_transfers_reminder_due_date(self):
        """Test that scheduling via mail.activity.schedule wizard passes reminder_due_date to created mail.activity."""
        partner = self.env['res.partner'].create({'name': 'Test Partner'})
        wizard = self.env['mail.activity.schedule'].create({
            'res_model': 'res.partner',
            'res_ids': str([partner.id]),
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': 'Wizard Test Activity',
            'reminder_due_date': fields.Date.today(),
            'date_deadline': fields.Date.today(),
            'activity_user_id': self.test_user.id,
        })
        activities = wizard._action_schedule_activities()
        self.assertTrue(activities, "Activity should be created by wizard")
        self.assertEqual(activities.reminder_due_date, fields.Date.today(), "Reminder due date must be copied from wizard to mail.activity")

    def test_wizard_schedule_activities_personal(self):
        """Test that scheduling personal activity via wizard transfers reminder_due_date."""
        partner = self.env['res.partner'].create({'name': 'Test Partner Personal'})
        wizard = self.env['mail.activity.schedule'].create({
            'res_model': 'res.partner',
            'res_ids': str([partner.id]),
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': 'Personal Activity Test',
            'reminder_due_date': fields.Date.today(),
            'date_deadline': fields.Date.today(),
            'activity_user_id': self.test_user.id,
        })
        activity = wizard._action_schedule_activities_personal()
        self.assertTrue(activity, "Personal activity should be created by wizard")
        self.assertEqual(activity.reminder_due_date, fields.Date.today(), "Reminder due date must be copied to personal activity")

    def test_wizard_without_reminder_due_date(self):
        """Test wizard scheduling without setting reminder_due_date completes normally."""
        partner = self.env['res.partner'].create({'name': 'Test Partner No Reminder'})
        wizard = self.env['mail.activity.schedule'].create({
            'res_model': 'res.partner',
            'res_ids': str([partner.id]),
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': 'No Reminder Activity',
            'date_deadline': fields.Date.today(),
            'activity_user_id': self.test_user.id,
        })
        activities = wizard._action_schedule_activities()
        self.assertTrue(activities)
        self.assertFalse(activities.reminder_due_date)

    def test_activity_cron_future_and_sent_reminders(self):
        """Test that cron ignores future reminders, already-sent reminders, and inactive activities."""
        # Future reminder (due tomorrow)
        future_date = fields.Date.add(fields.Date.today(), days=1)
        future_act = self.env['mail.activity'].create({
            'summary': 'Future Activity Reminder Test',
            'reminder_due_date': future_date,
            'date_deadline': future_date,
            'user_id': self.test_user.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': self.test_user.partner_id.id,
        })

        # Already sent reminder
        sent_act = self.env['mail.activity'].create({
            'summary': 'Already Sent Activity Reminder Test',
            'reminder_due_date': fields.Date.today(),
            'reminder_sent': True,
            'date_deadline': fields.Date.today(),
            'user_id': self.test_user.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': self.test_user.partner_id.id,
        })

        # Inactive activity
        inactive_act = self.env['mail.activity'].create({
            'summary': 'Inactive Activity Reminder Test',
            'reminder_due_date': fields.Date.today(),
            'active': False,
            'date_deadline': fields.Date.today(),
            'user_id': self.test_user.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': self.test_user.partner_id.id,
        })

        # Run cron
        self.env['mail.activity'].activity_cron()

        # Verify none of these activities had reminders sent
        self.assertFalse(future_act.reminder_sent, "Future activity should not have reminder_sent set to True")
        self.assertTrue(sent_act.reminder_sent, "Already sent activity should remain True")
        self.assertFalse(inactive_act.reminder_sent, "Inactive activity should not have reminder_sent set to True")

        # Verify no reminder emails were generated for these subjects
        unwanted_mails = self.env['mail.mail'].search([
            ('subject', 'ilike', 'Reminder: Activity %Activity Reminder Test%')
        ])
        self.assertFalse(unwanted_mails, "No reminder email should be created for future, sent, or inactive activities")

    def test_activity_cron_missing_user_email(self):
        """Test that cron gracefully skips activities where the assigned user has no email."""
        user_without_email = self.env['res.users'].create({
            'name': 'No Email User',
            'login': 'no_email_user',
            'email': False,
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        self.env['mail.activity'].create({
            'summary': 'No Email Activity',
            'reminder_due_date': fields.Date.today(),
            'date_deadline': fields.Date.today(),
            'user_id': user_without_email.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': user_without_email.partner_id.id,
        })

        # Run cron - should not raise exception
        self.env['mail.activity'].activity_cron()

    def test_activity_cron_batch_processing(self):
        """Test that multiple due activities are processed together and all marked as sent."""
        act1 = self.env['mail.activity'].create({
            'summary': 'Batch Activity 1',
            'reminder_due_date': fields.Date.today(),
            'date_deadline': fields.Date.today(),
            'user_id': self.test_user.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': self.test_user.partner_id.id,
        })
        act2 = self.env['mail.activity'].create({
            'summary': 'Batch Activity 2',
            'reminder_due_date': fields.Date.today(),
            'date_deadline': fields.Date.today(),
            'user_id': self.test_user.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': self.test_user.partner_id.id,
        })

        self.env['mail.activity'].activity_cron()
        self.assertTrue(act1.reminder_sent, "Batch activity 1 should be marked as sent")
        self.assertTrue(act2.reminder_sent, "Batch activity 2 should be marked as sent")

    def test_security_group_view_access(self):
        """Test that the reminder group only restricts reminder_due_date, while standard users can still use the wizard."""
        alarm_group = self.env.ref('activity_reminder.group_set_activity_alarm')
        self.assertTrue(alarm_group, "Security group group_set_activity_alarm must exist")

        # Create a standard user who does NOT have the alarm group
        standard_user = self.env['res.users'].create({
            'name': 'Standard Non-Alarm User',
            'login': 'std_non_alarm_user',
            'email': 'std_user@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        self.assertNotIn(alarm_group, standard_user.group_ids)

        # Standard user without group can freely open wizard and schedule activities
        partner = self.env['res.partner'].create({'name': 'Test Partner Wizard Access'})
        wizard_std = self.env['mail.activity.schedule'].with_user(standard_user).create({
            'res_model': 'res.partner',
            'res_ids': str([partner.id]),
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': 'Standard User Wizard Activity',
            'date_deadline': fields.Date.today(),
            'activity_user_id': standard_user.id,
        })
        activity = wizard_std._action_schedule_activities()
        self.assertTrue(activity, "Standard user without alarm group must still be able to schedule activities")
        self.assertFalse(activity.reminder_due_date, "Standard user activity should not have reminder_due_date")

        # Grant group to test user and verify view rendering
        self.test_user.write({'group_ids': [(4, alarm_group.id)]})
        self.assertIn(alarm_group, self.test_user.group_ids, "User should have the group assigned")

        wizard_view = self.env['mail.activity.schedule'].with_user(self.test_user).get_view(
            view_id=self.env.ref('activity_reminder.mail_activity_schedule_view_form_inherit_activity_reminder').id,
            view_type='form'
        )
        self.assertIn('reminder_due_date', wizard_view['arch'], "reminder_due_date should be in view arch for authorized user")


