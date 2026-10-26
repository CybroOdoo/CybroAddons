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
from datetime import datetime
from odoo import api, fields, models


class Task(models.Model):
    """Inherit 'project.task' to enable automatic task timers."""
    _inherit = 'project.task'

    task_timer = fields.Boolean(
        string='Timer',
        default=False,
        help='Activated when task is in the configured stage.'
    )
    is_user_working = fields.Boolean(
        string='Is Current User Working',
        compute='_compute_is_user_working',
        help='Technical field indicating whether the current user is working.'
    )
    duration = fields.Float(
        string='Real Duration',
        store=True,
        copy=False,
        compute='_compute_duration',
        help='Shows the total duration in minutes.'
    )
    is_status_stage = fields.Boolean(
        string='Stage Status',
        help='Indicates if the task is in the configured stage upon timer configuration.'
    )
    check_stage = fields.Integer(
        string='Configured Stage',
        compute='_compute_check_stage',
        help='Configured stage ID for the task project.'
    )

    @api.depends('task_timer', 'stage_id', 'project_id')
    def _compute_duration(self):
        """Compute active timer duration in minutes, reset to 0 in other stages."""
        for task in self:
            if task.task_timer:
                task.duration = task.get_working_duration()
            else:
                task.duration = 0.0

    @api.depends('project_id')
    def _compute_check_stage(self):
        """Assign the configured stage ID to check_stage."""
        for rec in self:
            if rec.project_id:
                config = self.env['timer.configuration'].search(
                    [('project_id', '=', rec.project_id.id)], limit=1
                )
                rec.check_stage = config.stage_id.id if config else 0
            else:
                rec.check_stage = 0

    @api.depends_context('uid')
    @api.depends('timesheet_ids.user_id', 'timesheet_ids.date_end')
    def _compute_is_user_working(self):
        """Check whether the current user is actively working on the task."""
        current_uid = self.env.user.id
        for task in self:
            task.is_user_working = any(
                line.user_id.id == current_uid and not line.date_end
                for line in task.timesheet_ids
            )

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        tasks._update_task_timer_stage()
        return tasks

    def write(self, vals):
        res = super().write(vals)
        if 'stage_id' in vals or 'project_id' in vals:
            self._update_task_timer_stage()
        elif 'task_timer' in vals:
            self._handle_timer_toggle()
        return res

    def _update_task_timer_stage(self):
        """Check the status of timer setting and update task_timer."""
        timer_setting = self.env['ir.config_parameter'].sudo().get_bool(
            'automatic_project_task_timer.timer_setting'
        )
        for task in self:
            is_timer_stage = False
            if timer_setting and task.project_id:
                config = self.env['timer.configuration'].search(
                    [('project_id', '=', task.project_id.id)], limit=1
                )
                if config and task.stage_id == config.stage_id:
                    is_timer_stage = True
            vals_to_write = {}
            if task.task_timer != is_timer_stage:
                vals_to_write['task_timer'] = is_timer_stage
            if task.is_status_stage:
                vals_to_write['is_status_stage'] = False
            if vals_to_write:
                task.write(vals_to_write)

    def _handle_timer_toggle(self):
        """Start or stop timesheet lines when task_timer changes."""
        time_line_obj = self.env['account.analytic.line']
        now = fields.Datetime.now()
        for rec in self:
            if rec.task_timer:
                open_lines = time_line_obj.search([
                    ('task_id', '=', rec.id),
                    ('user_id', '=', self.env.user.id),
                    ('date_end', '=', False),
                ])
                if not open_lines:
                    company = rec.company_id or self.env.company
                    employee = self.env['hr.employee'].sudo().search([
                        ('user_id', '=', self.env.user.id),
                        ('company_id', '=', company.id),
                    ], limit=1)
                    if not employee:
                        employee = self.env['hr.employee'].sudo().create({
                            'name': self.env.user.name,
                            'user_id': self.env.user.id,
                            'company_id': company.id,
                        })
                    time_line_obj.create({
                        'name': f"{self.env.user.name} : {rec.name}",
                        'task_id': rec.id,
                        'user_id': self.env.user.id,
                        'employee_id': employee.id,
                        'project_id': rec.project_id.id,
                        'date_start': now,
                    })
            else:
                open_lines = time_line_obj.search([
                    ('task_id', '=', rec.id),
                    ('date_end', '=', False),
                ])
                for time_line in open_lines:
                    start = time_line.date_start or now
                    diff = now - start
                    total_seconds = max(diff.total_seconds(), 0)
                    time_line.write({
                        'date_end': now,
                        'date_start': start,
                        'timer_duration': round(total_seconds / 60.0, 2),
                        'unit_amount': round(total_seconds / 3600.0, 2),
                    })
                rec.duration = 0.0

    def toggle_start(self):
        """Toggle timer active state."""
        for task in self:
            task.write({'task_timer': not task.task_timer})

    def get_working_duration(self):
        """Get the additional duration for productivity lines with no date_end."""
        self.ensure_one()
        duration = 0.0
        now = fields.Datetime.now()
        for time in self.timesheet_ids.filtered(lambda t: not t.date_end):
            if not isinstance(time.date_start, datetime):
                time.date_start = now
            else:
                duration += (now - time.date_start).total_seconds() / 60.0
        return duration
