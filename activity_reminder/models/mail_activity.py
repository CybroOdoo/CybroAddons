# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class MailActivity(models.Model):
    """inheriting to add fields"""
    _inherit = 'mail.activity'

    reminder_due_date = fields.Date(string='Reminder Due Date',
                                    help='Reminder due date')

    def activity_cron(self):
        """Scheduling a cron job to identify activities
        with a reminder due date matching the current date."""
        activities = self.env['mail.activity'].search(
            [('reminder_due_date', '=', fields.date.today())])
        for activity in activities:
                mail_values = {
                    'subject': 'Reminder: Activity {} is due '
                               '{}.'.format(activity.summary,
                                activity.date_deadline),
                    'body_html': 'This is a reminder that '
                                 'activity  {}'
                                 'is due {}. Please take action'
                                 ' accordingly.Its due date is '
                                 '{}.'.format(activity.summary,
                                              activity.date_deadline,
                                              activity.date_deadline),
                    'email_from': self.env.user.email,
                    'email_to': activity.user_id.email,
                }
                self.env['mail.mail'].create(mail_values).send()
