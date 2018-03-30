# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ReAssignTask(models.TransientModel):
    _name = 'task.reassign'

    pending_tasks = fields.One2many('pending.task', related='leave_req_id.pending_tasks', string='Pending Tasks')
    leave_req_id = fields.Many2one('hr.holidays', string='Leave Request')

    @api.multi
    def action_approve(self):
        task_pending = False
        e_unavail = False
        emp_unavail = []
        for task in self.pending_tasks:
            if not task.assigned_to:
                task_pending = True
        if task_pending:
            raise UserError(_('Please assign pending task to employees.'))
        else:
            for task in self.pending_tasks:
                if task.assigned_to in task.unavailable_employee:
                    emp_unavail.append(task.assigned_to.name)
                    e_unavail = True
            emp_unavail = set(emp_unavail)
            emp_unavail_count = len(emp_unavail)
            if e_unavail:
                if emp_unavail_count == 1:
                    raise UserError(_('Selected employee %s is not available') % (', '.join(emp_unavail),))
                else:
                    raise UserError(_('Selected employees %s are not available') % (', '.join(emp_unavail),))

            else:
                manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
                holiday = self.leave_req_id
                tasks = self.env['project.task']
                for task in self.pending_tasks:
                    if not task.assigned_to.user_id:
                        raise UserError(_('Please configure user for the employee %s') % (task.assigned_to.name,))
                    vals = {
                        'name': task.name,
                        'user_id': task.assigned_to.user_id.id,
                        'project_id': task.project_id.id,
                        'description': task.description,
                    }
                    tasks.sudo().create(vals)
                if holiday.double_validation:
                    return holiday.write({'state': 'validate1', 'manager_id': manager.id if manager else False})
                else:
                    holiday.action_validate()

    @api.multi
    def cancel(self):
        for task in self.pending_tasks:
            task.update({'assigned_to': False})
        return {'type': 'ir.actions.act_window_close'}
