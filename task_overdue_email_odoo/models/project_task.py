# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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


class ProjectTask(models.Model):
    """This is an Odoo model for Project Tasks. It inherits from the
    'project.task' model and adds a boolean field to indicate whether a task has
    been completed or not."""
    _inherit = 'project.task'

    completed_task = fields.Boolean(string='Task Completed',
                                    help="This field is used to indicate whether or not a particular task has been completed")

    def action_task_completed(self):
        """Onclicking Task Completed Button the Boolean field completed_task will become True and make Button
        Invisible"""
        self.completed_task = True

    def action_overdue(self):
        """ This is a Scheduled action  function that sends an email notification to project team members for overdue
        tasks. Reads a configuration parameter to determine the number of days after the due date that a task is
        considered overdue. Searches for incomplete tasks that have a due date less than or equal to the current
        date, and groups them by user For each user with overdue tasks, sends an email containing a list of their tasks.
        """
        over_due_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'task_overdue_email_odoo.overdue_days'))
        today = fields.date.today()
        project_task = self.env['project.task'].search(
            [('completed_task', '=', False), ('date_deadline', '<=', today)])
        user_tasks = {}
        for task in project_task:
            overdue_task_sent_mail = (today - task.date_deadline).days
            if overdue_task_sent_mail == over_due_days:
                for user in task.user_ids:
                    if user.email not in user_tasks:
                        user_tasks[user.email] = []
                    user_tasks[user.email].append((task.project_id.name,
                                                   task.name,
                                                   task.date_deadline,
                                                   user.name))

        for user_email, tasks in user_tasks.items():
            recipient_list = [(task[0], task[1], user_email) for task in tasks]
            project_name, task_name, task_deadline, user_name = tasks[0]
            email_values = {
                'recipient_list': recipient_list,
                'user_email': user_email,
                'task_deadline': task_deadline,
                'user_name': user_name,
            }
            template_id = self.env.ref \
                ('task_overdue_email_odoo.overdue_task_email_template').id
            self.env['mail.template'].browse(template_id).with_context(
                email_values) \
                .send_mail(self.id, force_send=True)
