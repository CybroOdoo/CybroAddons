# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
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
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    """
    Inherits from 'project.task' to add custom checklist support,
    document counting, and task categorization for the advanced
    project management system.
    """
    _inherit = 'project.task'

    document_count = fields.Integer(string='Documents',
                                    compute='_compute_document_count',
                                    help="For getting document count")
    checklist_template_ids = fields.Many2many(
        'project.task.checklist.template',
        string='Checklist', help="For adding project checklist template")
    checklist_info_ids = fields.One2many('project.task.checklist.info',
                                         'task_id', string="Checklist Info",
                                         help="For getting project checklist "
                                              "details")
    checklist_progress = fields.Float(
        string='Checklist Completed',
        help="For tracking checklist progress"
    )
    task_type = fields.Selection([
        ('task', 'Task'),
        ('subtask', 'Subtask'),
        ('bug', 'Bug'),
    ], string='Task Type', default="task")
    # ---------------------------------------------------------
    # Compute methods
    # ---------------------------------------------------------

    def _compute_document_count(self):
        """
        Computes the number of documents (attachments) associated with the task.
        """
        for rec in self:
            attachment_ids = self.env['ir.attachment'].search(
                [('res_model', '=', 'project.task'), ('res_id', '=', rec.id)])
            rec.document_count = len(attachment_ids)

    # ---------------------------------------------------------
    # Onchange methods
    # ---------------------------------------------------------

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """
        Automatically assigns the task to users specified in the new stage.
        """
        if self.stage_id.user_ids:
            self.user_ids = self.stage_id.user_ids

    @api.onchange('checklist_template_ids')
    def _onchange_checklist_template_ids(self):
        """
        Updates the checklist items when a checklist template is selected.
        """
        check_list_id = self.env['project.task.checklist.template'].browse(
            self.checklist_template_ids.ids)
        if check_list_id:
            for checklist_id in check_list_id.checklist_ids.ids:
                self.update({
                    'checklist_info_ids':
                        [(0, 0, {
                            'checklist_id': checklist_id
                        })]
                })

    # ---------------------------------------------------------
    # Constraint methods
    # ---------------------------------------------------------

    @api.constrains('checklist_progress')
    def _check_checklist_progress(self):
        """
        Validates that the checklist progress is within the valid range (0-1).
        :raises ValidationError: if progress is outside [0, 1].
        """
        for rec in self:
            if rec.checklist_progress < 0 or rec.checklist_progress > 1:
                raise ValidationError(
                    "Checklist progress must be between 0 and 1."
                )

    # ---------------------------------------------------------
    # Action methods
    # ---------------------------------------------------------

    def action_task_document(self):
        """
        Opens a kanban/form view of documents attached to the current task.
        :return: action dictionary.
        """
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,form',
            'res_id': self._origin.id,
            'domain': [
                ('res_id', '=', self._origin.id),
                ('res_model', '=', 'project.task')],
        }

    def task_mass_update(self):
        """
        Opens the wizard for mass updating task details.
        :return: action dictionary.
        """
        return {
            'name': 'Mass Update Tasks',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.mass.update',
            'target': 'new',
            'view_mode': 'form',
        }

    def task_overdue_notification(self):
        """
        Sends email notifications to responsible users for overdue tasks.
        This method is designed to be called via a scheduled action.
        """
        if self.env['ir.config_parameter'].sudo().get_param(
                'res.config.settings.is_overdue_notification'):
            task_ids = self.search([])
            for task in task_ids:
                if task.stage_id.name not in (
                        'Done',
                        'Canceled') and task.date_deadline and task.date_deadline < fields.Date.today():
                    mail_template = task.env.ref(
                        'advanced_project_management_system.task_due_email_notification')
                    mail_template.send_mail(task.id, force_send=True)

    # ---------------------------------------------------------
    # Private methods
    # ---------------------------------------------------------

    def _get_user_emails(self):
        """
        Collects email addresses of users assigned to overdue tasks.
        :return: A list of user login/email strings.
        """
        emails = []
        task_ids = self.search([('date_deadline', '<', fields.Date.today())])
        for task in task_ids:
            if task.stage_id.name not in ('Done', 'Canceled'):
                for user in task.user_ids:
                    emails.append(user.login)
        return emails
