# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class ProjectTask(models.Model):
    """ Inherits project Task to add fields and to show all free resources
    for the project based on the project start and end dates"""
    _inherit = 'project.task'

    task_start_date = fields.Date(string="Start Date",
                                  help='Start date of the task')
    manager_id = fields.Many2one('res.users',
                                 string='Project Manager',
                                 related='project_id.user_id',
                                 readonly=True,
                                 help='Project Manager of the task')

    @api.onchange('task_start_date', 'date_deadline')
    def _onchange_dates_user_domain(self):
        if not self.task_start_date or not self.date_deadline:
            return

        busy_ids = self.env['project.task'].get_busy_user_ids(
            self.task_start_date,
            self.date_deadline,
            exclude_task_id=self.id
        )

        domain = [('id', 'not in', busy_ids), ('share', '=', False)]

        if self.project_id.privacy_visibility == 'followers':
            domain.append((
                'id', 'in',
                self.project_id.message_follower_ids
                .mapped('partner_id.user_ids').ids
            ))

        return {'domain': {'user_ids': domain}}

    def get_busy_user_ids(self, from_date, end_date, exclude_task_id=None):
        """Function to get the BUSY user IDs for the particular period

        Args:
            from_date: Start date of the period
            end_date: End date of the period
            exclude_task_id: Optional task ID to exclude from search (for editing existing tasks)

        Returns:
            list: IDs of users who are busy (have tasks) during this period
        """
        busy_user_ids = set()
        domain = []
        if exclude_task_id:
            domain.append(('id', '!=', exclude_task_id))

        all_tasks = self.env['project.task'].search(domain)

        for task in all_tasks:
            if task.task_start_date:
                task_start = task.task_start_date

            else:
                task_start = None
            if task.date_deadline:
                task_end = task.date_deadline.date() if hasattr(task.date_deadline, 'date') else task.date_deadline
            else:
                task_end = None
            is_busy = False

            if task_start and task_end:
                if task_start <= end_date and task_end >= from_date:
                    is_busy = True
            elif task_start and not task_end:
                if task_start <= end_date:
                    is_busy = True
            elif task_end and not task_start:
                if task_end >= from_date:
                    is_busy = True

            if is_busy:
                if task.manager_id:
                    busy_user_ids.add(task.manager_id.id)
                for user in task.user_ids:
                    busy_user_ids.add(user.id)

        return list(busy_user_ids)
