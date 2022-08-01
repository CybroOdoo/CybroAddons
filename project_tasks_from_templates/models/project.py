# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technogies @cybrosys(odoo@cybrosys.com)
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
#############################################################################

from odoo import models, fields, api, _


class Project(models.Model):
    _inherit = 'project.project'

    project_template_id = fields.Many2one('project.task.template')

    def create_task(self, item, parent):
        vals = {'project_id': self.id,
                'name': item.name,
                'parent_id': parent,
                'stage_id': self.env['project.task.type'].search([('sequence', '=', 1)], limit=1).id,
                'user_ids': item.user_ids,
                'description': item.description
                }
        task_id = self.env['project.task'].create(vals).id
        for sub_task in item.child_ids:
            self.create_task(sub_task, task_id)

    def action_create_project_from_template(self):
        template_id = self.project_template_id
        for item in template_id.task_ids:
            self.create_task(item, False)
        return {
            'view_mode': 'form',
            'res_model': 'project.project',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': self._context
        }


class ProjectTaskCustom(models.Model):
    _name = 'project.task.custom'

    name = fields.Char("Name", required=True)
    project_template_id = fields.Many2one('project.task.template')
    description = fields.Text("Task Description")
    user_ids = fields.Many2many('res.users', relation='project_task_custom_user_rel', column1='task_id',
                                column2='user_id',
                                string='Assignees', tracking=True)
    parent_id = fields.Many2one('project.task.custom', string='Parent Task', index=True)
    child_ids = fields.One2many('project.task.custom', 'parent_id', string="Sub-tasks")

    def action_open_task(self):
        return {
            'view_mode': 'form',
            'res_model': 'project.task.custom',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': self._context
        }


class ProjectTaskTemplate(models.Model):
    _name = 'project.task.template'

    name = fields.Char("Template name", translate=True)
    task_ids = fields.One2many('project.task.custom', 'project_template_id', string="Tasks")
