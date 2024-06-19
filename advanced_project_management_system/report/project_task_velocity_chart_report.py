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


class ProjectVelocityChartReport(models.AbstractModel):
    """
       Abstract model for the Velocity Chart report.
       This model is used to calculate and display the Velocity Chart report
       for a specific project and task.
       """
    _name = 'project.velocity.chart.report'
    _description = 'Velocity Chart'

    date = fields.Date(string='Sprint Start Date', readonly=True,
                       help="The start date of the sprint.")
    completed_story_points = fields.Float(string='Completed Story Points',
                                          readonly=True,
                                          help="The total story points"
                                               " completed in the sprint.")



    @api.model
    def _read_group_raw(self, domain, fields, groupby, offset=0, limit=None,
                        orderby=False, lazy=True):
        """Compute grouped data for the Velocity Chart report."""
        data = []
        project_id = self._context.get('active_id')
        if groupby:
            tasks = self.env['project.task'].search([
                ('project_id', '=', project_id),
                ('stage_id.name', '=', 'Done')
            ])
            completed_within_deadline_count = defaultdict(
                lambda: defaultdict(int))
            completed_names = defaultdict(list)
            for task in tasks:
                sprint_start_date = task.create_date.date()
                completion_date = task.date_deadline or task.create_date.date()
                if task.stage_id.name == 'Done':
                    month_year = completion_date.strftime('%B %Y')
                    completed_within_deadline_count[month_year]['Total'] += 1
                    if sprint_start_date != completion_date:
                        completed_within_deadline_count[month_year][
                            'Start'] += 1
                    completed_names[month_year].append(task.name)
                for month_year, counts in completed_within_deadline_count.items():
                    data.append({
                        'date:month': [0, month_year],
                        'stage_id': True,
                        'completed_count': "\n".join(
                            completed_names[month_year]),
                        '__count': counts['Total'],
                        'date_start': counts['Start'],
                        '__domain': domain
                    })
        return data
