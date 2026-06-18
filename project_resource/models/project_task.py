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
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    """ Inherits project Task to add fields and to show all free resources
    for the project based on the project start and end dates"""
    _inherit = 'project.task'

    task_start_date = fields.Date(string="Start Date",
                                  help='Start date of the task')
    users_ids = fields.Many2many('res.users',
                                 compute="_compute_users_ids",
                                 help="This field is to store the users"
                                      " based on the calculation")
    manager_id = fields.Many2one('res.users',
                                 string='Project Manager',
                                 related='project_id.user_id',
                                 readonly=True,
                                 help='Project Manager of the task')

    @api.constrains('task_start_date', 'date_deadline')
    def _check_dates_deadline(self):
        """Ensure the deadline date is not earlier than the task start date."""
        for rec in self:
            if rec.task_start_date and rec.date_deadline:
                deadline = rec.date_deadline.date() if hasattr(rec.date_deadline, 'date') else rec.date_deadline
                if deadline < rec.task_start_date:
                    raise ValidationError("The deadline date must be after or equal to the task start date.")

    @api.constrains('user_ids', 'task_start_date', 'date_deadline')
    def _check_assignees_availability(self):
        """Ensure assigned users are free during the selected period.
        If dates are not set yet (e.g. during Kanban quick-create),
        we skip the validation. When dates are eventually set, we ensure
        the assigned users are free.
        """
        for rec in self:
            if rec.task_start_date and rec.date_deadline and rec.user_ids:
                start_date = rec.task_start_date
                end_date = rec.date_deadline.date() if hasattr(rec.date_deadline, 'date') else rec.date_deadline
                
                # First ensure deadline >= start_date (handled by the _check_dates_deadline constraint too)
                if end_date < start_date:
                    raise ValidationError("The deadline date must be after or equal to the task start date.")
                
                # Retrieve busy users for the period, excluding the current task
                busy_user_ids = rec.get_free_resource_ids(start_date, end_date, exclude_task_id=rec.id)
                
                # Check if any assigned user is in the busy users set
                busy_assignees = rec.user_ids.filtered(lambda u: u.id in busy_user_ids)
                if busy_assignees:
                    names = ", ".join(busy_assignees.mapped('name'))
                    raise ValidationError(
                        f"The following assignees are busy/occupied during the period {start_date} to {end_date}: {names}.\n"
                        "Please select resources that are free."
                    )

    def _get_project_visibility_user_domain(self, project):
        """Helper to get user domain based on project privacy_visibility settings."""
        if not project:
            return [('share', '=', False), ('active', '=', True)]
            
        followers_user_ids = project.message_follower_ids.mapped('partner_id.user_ids').ids
        visibility = project.privacy_visibility
        
        if visibility == 'followers':
            return [('share', '=', False), ('active', '=', True), ('id', 'in', followers_user_ids)]
        elif visibility == 'invited_users':
            return [('active', '=', True), ('id', 'in', followers_user_ids)]
        elif visibility == 'employees':
            return [('share', '=', False), ('active', '=', True)]
        elif visibility == 'portal':
            return [('active', '=', True), '|', ('share', '=', False), ('id', 'in', followers_user_ids)]
        else:
            return [('share', '=', False), ('active', '=', True)]

    @api.depends('task_start_date', 'date_deadline', 'project_id')
    def _compute_users_ids(self):
        """ Returning the domain for selecting the free resource """
        for rec in self:
            domain = rec._get_project_visibility_user_domain(rec.project_id)
            if rec.task_start_date and rec.date_deadline:
                start_date = rec.task_start_date
                end_date = rec.date_deadline.date() if hasattr(rec.date_deadline, 'date') else rec.date_deadline

                busy_resource_ids = self.env['project.task'].get_free_resource_ids(
                    start_date, end_date, exclude_task_id=rec.id)
                if busy_resource_ids:
                    domain = [('id', 'not in', busy_resource_ids)] + domain
            rec.users_ids = rec.env['res.users'].search(domain)

    def get_free_resource_ids(self, from_date, end_date, exclude_task_id=None):
        """Function to get the BUSY user IDs for the particular period

        Args:
            from_date: Start date of the period
            end_date: End date of the period
            exclude_task_id: Optional task ID to exclude from search (for editing existing tasks)

        Returns:
            list: IDs of users who are busy (have tasks) during this period
        """
        domain = [
            ('date_deadline', '!=', False),
            ('date_deadline', '>=', from_date),
        ]
        if exclude_task_id:
            domain.append(('id', '!=', exclude_task_id))

        if 'planned_date_begin' in self.env['project.task']._fields:
            domain += [
                '|',
                '&', ('task_start_date', '!=', False), ('task_start_date', '<=', end_date),
                '&', ('task_start_date', '=', False), '&', ('planned_date_begin', '!=', False), ('planned_date_begin', '<=', end_date)
            ]
        else:
            domain += [
                ('task_start_date', '!=', False),
                ('task_start_date', '<=', end_date)
            ]

        overlapping_tasks = self.env['project.task'].search(domain)
        return overlapping_tasks.mapped('user_ids').ids
