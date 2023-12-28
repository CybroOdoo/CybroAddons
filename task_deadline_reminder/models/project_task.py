# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ProjectTask(models.Model):
    """inherited to add reminder field"""
    _inherit = "project.task"

    is_task_reminder = fields.Boolean(string="Reminder",
                                      help='Task deadline reminder')

    @api.model
    def _cron_deadline_reminder(self):
        """Checks daily , if the task reaches deadline it will send the
        mail to assignee """
        task_id = self.search([('date_deadline', '!=', None),
                               ('is_task_reminder', '=', True),
                               ('user_ids', '!=', None)])
        today = fields.Date.today()
        for task in task_id:
            reminder_date = task.date_deadline.date()
            if reminder_date == today and task:
                template_id = self.env.ref(
                    'task_deadline_reminder.email_template_deadline_reminder')
                if template_id:
                    email_template_obj = self.env['mail.template'].browse(
                        template_id.id)
                    emails = [user.email for user in task.user_ids]
                    email_to = ', '.join(emails)
                    email_values = {
                        'email_to': email_to,
                        'email_cc': False,
                        'scheduled_date': False,
                        'recipient_ids': [],
                        'partner_ids': [],
                        'auto_delete': True,
                    }
                    email_template_obj.send_mail(
                        task.id, force_send=True, email_values=email_values)
        return True
