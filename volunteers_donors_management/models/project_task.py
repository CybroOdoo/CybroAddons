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
from odoo import api, fields, models


class ProjectTask(models.Model):
    """This class extends the 'project.task' model to add fields and follower
    management for storing volunteer details associated with a task."""
    _inherit = "project.task"

    project_task_partner_ids = fields.Many2many(
        'res.partner',
        string='Volunteer Details',
        help='The volunteers associated with this task',
        readonly=False)
    project_invisible_partner_ids = fields.Many2many(
        'res.partner',
        string="Project Volunteers",
        related='project_id.project_partner_ids')

    @api.onchange('project_task_partner_ids')
    def _onchange_project_task_partner_ids(self):
        """Automatically add followers when project_task_partner_ids changes on a saved task."""
        record = self._origin if self._origin else self
        if isinstance(record.id, int):
            record.message_subscribe(partner_ids=self.project_task_partner_ids.ids)

    @api.model_create_multi
    def create(self, vals_list):
        """Subscribe volunteers as followers upon task creation."""
        tasks = super().create(vals_list)
        for task in tasks:
            if task.project_task_partner_ids:
                task.message_subscribe(partner_ids=task.project_task_partner_ids.ids)
        return tasks

    def write(self, vals):
        """Override write to update volunteer followers when project_task_partner_ids changes.

        Only volunteers removed from the task are unsubscribed, ensuring project managers,
        authors, and assignees remain followers.
        """
        old_volunteers_by_task = {}
        if 'project_task_partner_ids' in vals:
            old_volunteers_by_task = {task.id: task.project_task_partner_ids for task in self}

        res = super().write(vals)

        if 'project_task_partner_ids' in vals:
            for task in self:
                old_volunteers = old_volunteers_by_task.get(task.id, self.env['res.partner'])
                new_volunteers = task.project_task_partner_ids
                added = new_volunteers - old_volunteers
                removed = old_volunteers - new_volunteers

                if added:
                    task.message_subscribe(partner_ids=added.ids)
                if removed:
                    keep_partners = task.user_ids.partner_id
                    if task.project_id.user_id.partner_id:
                        keep_partners |= task.project_id.user_id.partner_id
                    if task.partner_id:
                        keep_partners |= task.partner_id
                    to_unsubscribe = removed - keep_partners
                    if to_unsubscribe:
                        task.message_unsubscribe(partner_ids=to_unsubscribe.ids)
        return res
