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
from odoo import fields, models


class MailActivity(models.Model):
    """Inheriting persistent model 'mail.activity' to store reminder due date and execute cron."""
    _inherit = 'mail.activity'

    reminder_due_date = fields.Date(
        string='Reminder Due Date',
        help='Reminder due date')
    reminder_sent = fields.Boolean(
        string='Reminder Sent',
        default=False,
        copy=False)

    def activity_cron(self):
        """Scheduling a cron job to identify activities
        with a reminder due date matching or prior to the current date."""
        today = fields.Date.today()
        activities = self.search([
            ('reminder_due_date', '<=', today),
            ('reminder_sent', '=', False),
            ('active', '=', True),
        ])
        for activity in activities:
            recipient_email = activity.user_id.email
            if not recipient_email:
                continue

            sender_email = (
                self.env.user.email
                or self.env.company.email
                or self.env['res.users'].sudo().search([('email', '!=', False)], limit=1).email
            )
            if not sender_email:
                continue

            mail_values = {
                'subject': f'Reminder: Activity {activity.summary or ""} is due {activity.date_deadline}.',
                'body_html': (
                    f'This is a reminder that activity {activity.summary or ""} '
                    f'is due {activity.date_deadline}. Please take action accordingly.'
                ),
                'email_from': sender_email,
                'email_to': recipient_email,
            }
            self.env['mail.mail'].create(mail_values).send()
            activity.reminder_sent = True

