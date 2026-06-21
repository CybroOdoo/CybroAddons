# -*- coding: utf-8 -*-
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
        """Test that the activity_cron cron job finds due activity schedules and sends reminder emails."""
        # Clean/count existing mail messages/mails with this subject to ensure clear assertion
        initial_mail_count = self.env['mail.mail'].search_count([
            ('subject', 'like', 'Reminder: Activity Test Schedule is due')
        ])

        # Create a mail.activity.schedule (TransientModel) record with reminder_due_date = today
        schedule = self.env['mail.activity.schedule'].create({
            'summary': 'Test Schedule',
            'reminder_due_date': fields.Date.today(),
            'date_deadline': fields.Date.today(),
            'activity_user_id': self.test_user.id,
        })

        # Run the cron function
        self.env['mail.activity.schedule'].activity_cron()

        # Check if the mail was created
        sent_mails = self.env['mail.mail'].search([
            ('subject', 'like', 'Reminder: Activity Test Schedule is due')
        ])
        
        self.assertEqual(len(sent_mails), initial_mail_count + 1, "Exactly one reminder email should be created and sent")
        latest_mail = sent_mails[0]
        self.assertEqual(latest_mail.email_to, self.test_user.email)
        self.assertEqual(latest_mail.email_from, self.env.user.email)
