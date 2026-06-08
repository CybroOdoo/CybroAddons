# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError


class TaskReassign(models.TransientModel):
    """Module for task assignments"""
    _name = 'task.reassign'
    _description = 'Task Reassign'

    pending_task_ids = fields.One2many('pending.task',
                                       related='leave_req_id.pending_task_ids',
                                       string='Pending Tasks',
                                       help='List of pending tasks associated'
                                            ' with the leave request.',
                                       readonly=False)
    leave_req_id = fields.Many2one('hr.leave',
                                   string='Leave Request',
                                   help='Leave request to which the pending'
                                        ' tasks are related.')

    def action_approve(self):
        """Method for approve the tasks"""
        task_pending = False
        e_unavail = False
        emp_unavail = []
        for task in self.pending_task_ids:
            if not task.assigned_person_id:
                task_pending = True
        if task_pending:
            raise UserError(_('Please assign pending task to employees.'))
        for task in self.pending_task_ids:
            if task.assigned_person_id in task.unavailable_employee_ids:
                emp_unavail.append(task.assigned_person_id.name)
                e_unavail = True
        emp_unavail = set(emp_unavail)
        emp_unavail_count = len(emp_unavail)
        if e_unavail:
            if emp_unavail_count == 1:
                raise UserError(_('Selected employee %s is not available') % (', '.join(emp_unavail),))
            else:
                raise UserError(_('Selected employees %s are not available') % (
                ', '.join(emp_unavail),))
        else:
            holiday = self.leave_req_id
            tasks = self.env['project.task']
            for task in self.pending_task_ids:
                vals = {
                    'name': task.name,
                    'user_ids': [(3, task.assigned_person_id.user_id.id)],
                    'project_id': task.project_id.id,
                    'description': task.description,
                }
                tasks.sudo().create(vals)
                holiday._action_validate()

    def cancel(self):
        """Cancel function for the tasks"""
        for task in self.pending_task_ids:
            task.update({'assigned_person_id': False})
        return {'type': 'ir.actions.act_window_close'}
