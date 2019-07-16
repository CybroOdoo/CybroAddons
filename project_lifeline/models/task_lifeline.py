# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import fields, models
from dateutil.relativedelta import relativedelta


class TaskLifeline(models.Model):
    _inherit = 'project.task'

    lifeline = fields.Float(string="Life line", default='100', copy=False, readonly=True)
    date_deadline = fields.Datetime('Deadline', required=True)

    def process_lifeline_scheduler(self, cr, uid, context=None):
        task_obj = self.pool.get('project.task')
        task_ids = task_obj.search(cr, uid, [])
        time_now = fields.Datetime.from_string(fields.Datetime.now())
        for task_id in task_ids:
            task = task_obj.browse(cr, uid, task_id, context=context)
            start_date = fields.Datetime.from_string(task.date_assign)
            end_date = fields.Datetime.from_string(task.date_deadline)
            if task.stage_id and (task.stage_id.name == 'Done' or task.stage_id.name == 'Cancelled'):
                task.lifeline = 0
            else:
                if task.date_deadline and task.date_assign and end_date > start_date:
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
