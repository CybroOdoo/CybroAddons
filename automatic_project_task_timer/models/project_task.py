# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R(odoo@cybrosys.com)
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
###############################################################################
from datetime import datetime
from odoo import api, fields, models


class Task(models.Model):
    """inherited the 'project.task' for running the timer """
    _inherit = 'project.task'

    task_timer = fields.Boolean(string='Timer', default=False,
                                help='Activated when task configured stage')
    is_user_working = fields.Boolean(string='Is Current User Working',
                                     compute='_compute_is_user_working',
                                     help="Technical field indicating whether "
                                          "the current user is working. ")
    duration = fields.Float(string='Real Duration', store=True, copy=False,
                            readonly=False, help='Shows the duration')
    is_status_stage = fields.Boolean(string='Stage Status',
                                     help='To set the status of task at the '
                                          'initial time.')
    check_stage = fields.Integer(string='Stage',
                                 compute='_compute_check_stage',
                                 help='To check the stage whether it is '
                                      'configured or not')

    def _compute_check_stage(self):
        """To check the stage whether it is configured or not, for that
        assigning the configured stage id to this field."""
        for rec in self:
            rec.check_stage = self.env['timer.configuration'].search(
                [('project_id.id', '=', rec.project_id.id)]).stage_id.id

    @api.constrains('stage_id')
    def _task_timer(self):
        """Checks the status of timer setting and
        toggle the task timer boolean to active """
        self.write({
            'is_status_stage': False
        })
        timer_setting = self.env['ir.config_parameter'].sudo().get_param(
            'automatic_project_task_timer.timer_setting')
        if timer_setting:
            for rec in self.env['timer.configuration'].search([]):
                if self.project_id == rec.project_id:
                    if self.stage_id.id == rec.stage_id.id:
                        self.write({'task_timer': True})
                    else:
                        self.write({'task_timer': False})

    def _compute_is_user_working(self):
        """ Checks whether the current user is working """
        for order in self:
            if order.timesheet_ids.filtered(
                    lambda x: (x.user_id.id == self.env.user.id) and (
                            not x.date_end)):
                order.is_user_working = True
            else:
                order.is_user_working = False

    @api.model
    @api.constrains('task_timer')
    def toggle_start(self):
        """The time sheet record will be created
         by checking all the conditions """
        time_line_obj = self.env['account.analytic.line']
        for rec in self:
            if rec.task_timer is True:
                rec.write({'is_user_working': True})
                for time_sheet in rec:
                    time_line_obj.create({
                        'name': '%s : %s' % (self.env.user.name,
                                             time_sheet.name),
                        'task_id': time_sheet.id,
                        'user_id': self.env.user.id,
                        'project_id': time_sheet.project_id.id,
                        'date_start': datetime.now(),
                    })
            else:
                rec.write({'is_user_working': False})
                for time_line in time_line_obj.search(
                        [('task_id', 'in', self.ids),
                         ('date_end', '=', False)]):
                    time_line.write({'date_end': fields.Datetime.now()})
                    if time_line.date_start:
                        if time_line.date_end:
                            diff = fields.Datetime.from_string(
                                time_line.date_end) \
                                   - fields.Datetime.from_string(
                                time_line.date_start).replace(
                                second=0, microsecond=0)
                            time_line.timer_duration = \
                                round(diff.total_seconds() / 60.0, 2)
                            time_line.unit_amount = \
                                round(diff.total_seconds() / (60.0 * 60.0), 2)
                        else:
                            time_line.unit_amount = 0.0
                            time_line.timer_duration = 0.0
                    else:
                        time_line.write({'date_start': fields.Datetime.now()})
                        if time_line.date_end:
                            diff = fields.Datetime.from_string(
                                time_line.date_end) \
                                   - fields.Datetime.from_string(
                                time_line.date_start).replace(
                                second=0, microsecond=0)
                            time_line.timer_duration = \
                                round(diff.total_seconds() / 60.0, 2)
                            time_line.unit_amount = \
                                round(diff.total_seconds() / (60.0 * 60.0), 2)
                        else:
                            time_line.unit_amount = 0.0
                            time_line.timer_duration = 0.0

    def get_working_duration(self):
        """Get the additional duration for 'open times'
        i.e. productivity lines with no date_end."""
        self.ensure_one()
        duration = 0
        for time in \
                self.timesheet_ids.filtered(lambda time: not time.date_end):
            if type(time.date_start) != datetime:
                time.date_start = datetime.now()
                duration = 0
            else:
                duration += \
                    (datetime.now() - time.date_start).total_seconds() / 60
        return duration
