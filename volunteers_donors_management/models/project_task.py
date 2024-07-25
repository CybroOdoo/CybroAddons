# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nandakishore M (odoo@cybrosys.info)
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
from odoo import api, fields, models


class ProjectTask(models.Model):
    """  This class extends the 'project.task' model to add a many-to-many
    field for storing volunteer details associated with a task.

     Methods:
     _compute_followers(): Compute method to update task followers based on
        project_task_partner_ids.
    """
    _inherit = "project.task"

    project_task_partner_ids = fields.Many2many(
        'res.partner',
        string='Volunteer Details',
        help='The volunteers associated with this task',
        readonly=False)
    project_invisible_partner_ids = fields.Many2many(
        'res.partner', string="Project Volunteers",
        related='project_id.project_partner_ids', )

    @api.depends('project_invisible_partner_ids')
    def _compute_volunteer_domain(self):
        """Compute method to update project_task_partner_ids
             based on project_invisible_partner_ids."""
        for task in self:
            task.project_task_partner_ids = [
                (6, 0, task.project_invisible_partner_ids.ids)]

    @api.onchange('project_task_partner_ids')
    def _onchange_project_task_partner_ids(self):
        """Automatically add followers when project_task_partner_ids changes."""
        self.message_subscribe(partner_ids=self.project_task_partner_ids.ids)

    def write(self, vals):
        """
        Override the write method to handle changes in project_task_partner_ids.

        When the project_task_partner_ids field is updated, this method
        calculates the partner IDs that are being removed and unsubscribes
        them as followers.

        :param vals: A dictionary of field values to update.
        :return: The result of the original write method.
        """
        res = super(ProjectTask, self).write(vals)
        follower_ids = self.message_follower_ids.mapped('partner_id').ids
        task_partner_ids = self.project_task_partner_ids.ids
        user_ids = self.user_ids.mapped('partner_id').ids
        non_intersecting = set(task_partner_ids) ^ set(follower_ids)
        assignees_non_intersecting = set(user_ids) ^ non_intersecting
        partner_ids = self.env['res.partner'].browse(assignees_non_intersecting)
        self.message_unsubscribe(partner_ids=partner_ids.ids)
        return res
