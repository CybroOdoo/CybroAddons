# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nilmar Shereef(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields, models


class ProjectStages(models.Model):
    _inherit = 'project.task.type'

    freeze_state = fields.Boolean(string='Is Freeze State',
                                  help="Enable to stop the life line running at this Stages.")


class TaskLifeline(models.Model):
    _inherit = 'project.task'

    lifeline = fields.Float(string="Life line", default='100', copy=False, readonly=True)
    date_deadline_ext = fields.Datetime('Deadline', required=True)

    def process_lifeline_scheduler(self):
        task_obj = self.env['project.task']
        task_ids = task_obj.search([])
        time_now = fields.Datetime.from_string(fields.Datetime.now())
        for task in task_ids:
            start_date = fields.Datetime.from_string(task.date_assign)
            end_date = fields.Datetime.from_string(task.date_deadline_ext)
            if task.stage_id and task.stage_id.freeze_state != True:
                if task.date_deadline_ext and task.date_assign and end_date > start_date:
                    if time_now < end_date:
                        total_difference_days = relativedelta(end_date, start_date)
                        difference_minute = total_difference_days.hours * 60 + total_difference_days.minutes
                        date_difference = end_date - start_date
                        total_difference_minute = int(date_difference.days) * 24 * 60 + difference_minute

                        remaining_days = relativedelta(time_now, start_date)
                        remaining_minute = remaining_days.hours * 60 + remaining_days.minutes
                        date_remaining = time_now - start_date
                        total_minute_remaining = int(date_remaining.days) * 24 * 60 + remaining_minute
                        if total_difference_minute != 0:
                            task.lifeline = (100 - ((total_minute_remaining * 100) / total_difference_minute))
                        else:
                            task.lifeline = 0
                    else:
                        task.lifeline = 0