# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R (odoo@cybrosys.com)
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


class ProjectTask(models.Model):
    """Extending project task for additional timer functionality."""
    _inherit = 'project.task'

    task_timer = fields.Boolean(
        string='Timer', default=False,
        help="Field to indicate if the timer is active.")
    is_user_working = fields.Boolean(
        string='Is Current User Working', compute='_compute_is_user_working',
        help="Technical field indicating whether the current user is working.")
    duration = fields.Float(
        string='Real Duration', store=True, readonly=False,
        help="The actual duration of the project task.")
    timer_user_id = fields.Many2one('res.users', string="Timer User")
    show_timer = fields.Boolean(string="Timer", compute='_compute_show_timer',
                                help="Indicates whether the timer should be"
                                     " shown for the current user.")

    @api.depends('timer_user_id')
    def _compute_show_timer(self):
        """Compute the value of the show_timer field based on the
        timer_user_id."""
        for rec in self:
            if rec.timer_user_id:
                rec.show_timer = self.env.user.id == rec.timer_user_id.id
            else:
                rec.show_timer = True

    def _compute_is_user_working(self):
        """ Compute if the current user is working on the task """
        for order in self:
            if order.timesheet_ids.filtered(
                    lambda x: (x.user_id.id == self.env.user.id) and (
                            not x.date_end)):
                order.is_user_working = True
            else:
                order.is_user_working = False

    def action_toggle_start(self, timer):
        """ Toggle the timer based on the given parameter """
        if timer:
            self.write({'is_user_working': True, 'task_timer': True,
                        'timer_user_id': self.env.user.id})
            time_line = self.env['account.analytic.line']
            for time_sheet in self:
                time_line.create({
                    'name': self.env.user.name + ': ' + time_sheet.name,
                    'task_id': time_sheet.id,
                    'user_id': self.env.user.id,
                    'project_id': time_sheet.project_id.id,
                    'using_timer': True,
                    'date_start': fields.Datetime.now(),
                })
        else:
            self.write({'is_user_working': False, 'task_timer': False,
                        'timer_user_id': False})
            time_line_obj = self.env['account.analytic.line']
            domain = [('task_id', 'in', self.ids), ('date_end', '=', False),
                      ('user_id', '=', self.env.user.id)]
            for time_line in time_line_obj.search(domain):
                if time_line.date_start:
                    time_line.write({'date_end': fields.Datetime.now()})
                    diff = fields.Datetime.from_string(
                        time_line.date_end) - fields.Datetime.from_string(
                        time_line.date_start)
                    time_line.timer_duration = round(
                        diff.total_seconds() / 60.0, 2)
                    time_line.unit_amount = round(
                        diff.total_seconds() / (60.0 * 60.0), 2)

    def get_working_duration(self):
        """Get the additional duration for 'open times' i.e. productivity
        lines with no date_end."""
        self.ensure_one()
        duration = 0
        for time in self.timesheet_ids.filtered(
                lambda time: not time.date_end and time.using_timer):
            if type(time.date_start) != datetime:
                time.date_start = datetime.now()
                duration = 0
            else:
                duration += ((datetime.now() - time.date_start).total_seconds()
                             / 60)
        return duration
