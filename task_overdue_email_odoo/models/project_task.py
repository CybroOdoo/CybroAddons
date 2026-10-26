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


class ProjectTask(models.Model):
    """Add overdue email notifications to project tasks."""
    _inherit = 'project.task'

    def action_overdue(self):
        """This is a Scheduled action function that sends an email
        notification to project team members for overdue
        tasks. Reads a configuration parameter to determine the
        number of days after the due date that a task is
        considered overdue. Searches for incomplete tasks that have
        a due date less than or equal to the current
        date, and groups them by user. For each user with overdue tasks,
        sends an email containing a list of their tasks.
        """
        is_notification = self.env['ir.config_parameter'].sudo().get_bool(
            'task_overdue_email_odoo.is_notification')
        if not is_notification:
            return

        over_due_days = self.env['ir.config_parameter'].sudo().get_int(
            'task_overdue_email_odoo.overdue_days', default=0)

        today = fields.Datetime.now()
        project_tasks = self.env['project.task'].search([
            ('state', 'not in', ['1_done', '1_canceled']),
            ('date_deadline', '!=', False),
            ('date_deadline', '<=', today),
        ])

        user_tasks = {}
        for task in project_tasks:
            overdue_task_sent_mail = (today.date() - task.date_deadline.date()).days
            if overdue_task_sent_mail == over_due_days:
                for user in task.user_ids:
                    if user.email:
                        if user.email not in user_tasks:
                            user_tasks[user.email] = []
                        user_tasks[user.email].append((
                            task.project_id.name or '',
                            task.name or '',
                            fields.Date.to_string(task.date_deadline.date()),
                            user.name or '',
                            task.id,
                        ))

        template = self.env.ref(
            'task_overdue_email_odoo.overdue_task_email_template', raise_if_not_found=False)
        if not template:
            return
        for user_email, tasks in user_tasks.items():
            project_name, task_name, task_deadline, user_name, task_id = tasks[0]
            recipient_list = [(t[0], t[1], t[2]) for t in tasks]
            email_ctx = {
                'recipient_list': recipient_list,
                'user_email': user_email,
                'task_deadline': task_deadline,
                'user_name': user_name,
            }
            template.with_context(**email_ctx).send_mail(
                task_id,
                force_send=True,
                email_values={'email_to': user_email}
            )
