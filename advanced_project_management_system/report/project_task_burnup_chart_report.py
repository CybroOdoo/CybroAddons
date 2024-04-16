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
from collections import defaultdict
from odoo import fields, models, _


class ProjectTaskBurnupChartReport(models.AbstractModel):
    """This model defines the Burnup Chart report for project tasks. """
    _name = 'project.task.burnup.chart.report'
    _description = 'Burnup Chart'
    _auto = True

    project_id = fields.Many2one('project.project', readonly=True)
    date = fields.Datetime(string='Date', readonly=True,
                           help='The date of data entry')
    completed_count = fields.Integer(string='Completed Tasks', readonly=True,
                                     help='The number of completed tasks')
    total_count = fields.Integer(string='Total Tasks', readonly=True,
                                 help='The total number of tasks')

    def _read_group(self, domain, groupby=(), aggregates=(), having=(),
                    offset=0, limit=None, order=None):
        data = []
        project_id = self._context.get('active_id')

        if groupby:
            tasks = self.env['project.task'].search([
                ('project_id', '=', project_id),
                ('stage_id.name', '=', 'Done')
            ])

            task_counts = defaultdict(lambda: defaultdict(int))
            task_names = defaultdict(list)

            for task in tasks:
                completion_date = task.date_deadline or task.create_date.date()

                if isinstance(completion_date, fields.date):
                    completion_date = fields.datetime.combine(completion_date,
                                                                fields.datetime.min.time())
                    start_date = task.create_date.date()

                if task.stage_id.name == 'Done':
                    month_year = completion_date
                    task_counts[month_year]['Total'] += 1

                    if start_date != completion_date:
                        task_counts[month_year]['Start'] += 1
                    task_names[month_year].append(task.name)

            for month_year, counts in task_counts.items():
                data.append((month_year, task_names[month_year], counts['Total']))
        return data
