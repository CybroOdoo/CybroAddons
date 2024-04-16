# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ProjectTask(models.Model):
    """ Added checklist and document details"""
    _inherit = 'project.task'

    document_count = fields.Integer(string='Documents',
                                    compute='_compute_document_count',
                                    help="For getting document count")
    checklist_template_ids = fields.Many2many(
        'project.task.checklist.template',
        string='Checklist', help="For adding project checklist template")
    checklist_info_ids = fields.One2many('project.task.checklist.info',
                                         'task_id', string="checklist info",
                                         help="for getting project checklist "
                                              "details")
    checklist_progress = fields.Float(string='Checklist Completed',
                                      colors="red,orange,yellow,green",
                                      help="For tracking checklist progress",
                                      max_value=1, min_value=0)
    task_type = fields.Selection([
        ('task', 'Task'),
        ('subtask', 'Subtask'),
        ('bug', 'Bug'),
    ], string='Task Type', default="task")

    def task_overdue_notification(self):
        """ Scheduled action for email notification to
            employee about task due """
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

    def _get_user_emails(self):
        """ Return email ids of the employee"""
        emails = []
        task_ids = self.search([('date_deadline', '<', fields.Date.today())])
        for task in task_ids:
            if task.stage_id.name not in ('Done', 'Canceled'):
                for user in task.user_ids:
                    emails.append(user.login)
        return emails

    def _compute_document_count(self):
        """ Compute document count and return """
        for rec in self:
            attachment_ids = self.env['ir.attachment'].search(
                [('res_model', '=', 'project.task'), ('res_id', '=', rec.id)])
            rec.document_count = len(attachment_ids)

    def button_task_document(self):
        """ Return document kanban for the task"""
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
        """ Return wizard for updating task details"""
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.mass.update',
            'target': 'new',
            'view_mode': 'form',
        }

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """ While changing task stage task will automatically assign to
                                                    users from task stage"""
        if self.stage_id.user_ids:
            self.user_ids = self.stage_id.user_ids

    @api.onchange('checklist_template_ids')
    def _onchange_checklist_template_ids(self):
        """When the `checklist_template_ids` field is modified, this method is
        triggered to update the `checklist_info_ids` field.
        It browses the selected checklist templates and for each checklist item in these templates,
        it creates a new checklist info record linked to the current task.
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
