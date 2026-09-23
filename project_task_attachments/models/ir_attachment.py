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


class IrAttachment(models.Model):
    """Inherit IR attachment for adding extra fields and inheriting create
    function """
    _inherit = 'ir.attachment'

    attach_to = fields.Selection([('project', 'Project'),
                                  ('task', 'Task')],
                                 required=True, string="Attach To",
                                 help="if Project, file attached to Project."
                                      " Otherwise to task.", default='project')
    project_id = fields.Many2one('project.project',
                                 string='Project',
                                 help="This indicates the Project")
    task_id = fields.Many2one('project.task',
                              string='Task', help="This indicates the Task")

    def _auto_init(self):
        res = super()._auto_init()
        self.env.cr.execute("""
            UPDATE ir_attachment
            SET project_id = NULL
            WHERE project_id = 0;
            UPDATE ir_attachment
            SET task_id = NULL
            WHERE task_id = 0;
        """)
        return res

    def _prepare_vals(self, vals, record=None):
        vals = dict(vals)
        
        has_project_key = 'project_id' in vals
        has_task_key = 'task_id' in vals

        project_id = vals.get('project_id')
        task_id = vals.get('task_id')

        # Convert recordset objects to IDs if passed
        if hasattr(project_id, 'id'):
            project_id = project_id.id
        if hasattr(task_id, 'id'):
            task_id = task_id.id

        if project_id and isinstance(project_id, int) and project_id > 0:
            vals['project_id'] = project_id
            vals['res_model'] = 'project.project'
            vals['res_id'] = project_id
            vals['attach_to'] = 'project'
            vals['task_id'] = False
        elif task_id and isinstance(task_id, int) and task_id > 0:
            vals['task_id'] = task_id
            vals['res_model'] = 'project.task'
            vals['res_id'] = task_id
            vals['attach_to'] = 'task'
            vals['project_id'] = False
        elif has_project_key and not project_id:
            vals['project_id'] = False
            vals['task_id'] = False
            if 'res_id' not in vals and record and record.res_model == 'project.project':
                vals['res_id'] = 0
        elif has_task_key and not task_id:
            vals['task_id'] = False
            vals['project_id'] = False
            if 'res_id' not in vals and record and record.res_model == 'project.task':
                vals['res_id'] = 0
        else:
            res_model = vals.get('res_model') or (record and record.res_model)
            res_id = vals.get('res_id') if 'res_id' in vals else (record and record.res_id)
            
            if res_model == 'project.project':
                vals['attach_to'] = 'project'
                vals['project_id'] = res_id if (res_id and isinstance(res_id, int) and res_id > 0) else False
                vals['task_id'] = False
            elif res_model == 'project.task':
                vals['attach_to'] = 'task'
                vals['task_id'] = res_id if (res_id and isinstance(res_id, int) and res_id > 0) else False
                vals['project_id'] = False
            else:
                if 'project_id' in vals and not (vals['project_id'] and isinstance(vals['project_id'], int) and vals['project_id'] > 0):
                    vals['project_id'] = False
                if 'task_id' in vals and not (vals['task_id'] and isinstance(vals['task_id'], int) and vals['task_id'] > 0):
                    vals['task_id'] = False
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        """Supering the create function in order to set project_id/task_id and res_id/res_model correctly"""
        sanitized_vals_list = [self._prepare_vals(vals) for vals in vals_list]
        return super().create(sanitized_vals_list)

    def write(self, vals):
        """Supering the write function in order to sync project_id/task_id and res_id/res_model correctly"""
        for record in self:
            sanitized_vals = self._prepare_vals(vals, record=record)
            super(IrAttachment, record).write(sanitized_vals)
        return True

