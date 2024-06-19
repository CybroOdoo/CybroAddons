# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _


class ProjectTaskBurnupChartReport(models.AbstractModel):
    """This model defines the Burnup Chart report for project tasks. """
    _name = 'project.task.burnup.chart.report'
    _description = 'Burnup Chart'

    date = fields.Datetime(string='Date', readonly=True,
                           help='The date of data entry')
    completed_count = fields.Integer(string='Completed Tasks', readonly=True,
                                     help='The number of completed tasks')
    total_count = fields.Integer(string='Total Tasks', readonly=True,
                                 help='The total number of tasks')
    @api.model
    def _read_group_raw(self, domain, fields, groupby, offset=0,
                        limit=None, orderby=False, lazy=True):
        """Generate raw data for the Burnup Chart report."""
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
                start_date = task.create_date.date()
                if task.stage_id.name == 'Done':
                    month_year = completion_date.strftime('%B %Y')
                    task_counts[month_year]['Total'] += 1
                    if start_date != completion_date:
                        task_counts[month_year]['Start'] += 1
                    task_names[month_year].append(task.name)
            for month_year, counts in task_counts.items():
                data.append({
                    'date:month': [0, month_year],
                    'stage_id': True,
                    'completed_count': "\n".join(task_names[month_year]),
                    '__count': counts['Total'],
                    'date_start': counts['Start'],
                    '__domain': domain
                })
        return data
