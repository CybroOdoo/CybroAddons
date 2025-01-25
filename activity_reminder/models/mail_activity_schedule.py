# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class MailActivitySchedule(models.TransientModel):
    """Inheriting model  'mail.activity.schedule' to add fields"""
    _inherit = 'mail.activity.schedule'

    reminder_due_date = fields.Date(
        string='Reminder Due Date',
        help='Reminder due date',
        groups='activity_reminder.group_set_activity_alarm')

    def activity_cron(self):
        """Scheduling a cron job to identify activities
        with a reminder due date matching the current date."""
        # Manually add the group to the user
        activities = self.env['mail.activity.schedule'].search(
            [('reminder_due_date', '=', fields.date.today())])
        for activity in activities:
            mail_values = {
                'subject': 'Reminder: Activity {} is due '
                           '{}.'.format(activity.summary,
                                        activity.date_deadline),
                'body_html': 'This is a reminder that '
                             'activity  {}'
                             ' is due {}. Please take action'
                             ' accordingly.Its due date is '
                             '{}.'.format(activity.summary,
                                          activity.date_deadline,
                                          activity.date_deadline),
                'email_from': self.env.user.email,
                'email_to': activity.activity_user_id.email,
            }
            self.env['mail.mail'].create(mail_values).send()
