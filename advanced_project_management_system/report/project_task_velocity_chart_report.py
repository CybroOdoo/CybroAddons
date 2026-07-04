# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
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
from datetime import datetime,time,date
from collections import defaultdict
from odoo import api, fields, models


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
    def _read_group(self, domain, groupby=(), aggregates=(), having=(),
                    offset=0, limit=None, order=None):
        """
        Calculates and returns the aggregated velocity data for the chart.
        Groups tasks by their completion date and counts completed story points.
        """
        data = []
        project_id = self._context.get('active_id')

        if groupby:
            tasks = self.env['project.task'].search([
                ('project_id', '=', project_id),
                ('stage_id.name', '=', 'Done')
            ])

            completed_within_deadline_count = defaultdict(int)

            for task in tasks:
                # 🔹 Ensure both are datetime
                sprint_start_date = task.create_date
                completion_date = task.date_deadline or task.create_date

                # 🔹 If it's a 'date', make it datetime
                if isinstance(completion_date, date) and not isinstance(completion_date, datetime):
                    completion_date = datetime.combine(completion_date, time.min)

                if isinstance(sprint_start_date, date) and not isinstance(sprint_start_date, datetime):
                    sprint_start_date = datetime.combine(sprint_start_date, time.min)

                if task.stage_id.name == 'Done':
                    # 🔹 Use datetime (normalized) for grouping
                    month_year = datetime.combine(completion_date.date(), time.min)
                    completed_within_deadline_count[month_year] += 1

            # 🔹 Collect data
            for month_year, count in completed_within_deadline_count.items():
                # Odoo's _read_group expects a list of tuples where each tuple contains
                # groupby values followed by aggregate values.
                # The length of each tuple must be exactly len(groupby) + len(aggregates).
                res = [month_year] * len(groupby)
                for _ in aggregates:
                    res.append(count)
                data.append(tuple(res))

        return data
