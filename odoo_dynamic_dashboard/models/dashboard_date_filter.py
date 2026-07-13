# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DashboardDateFilter(models.Model):
    """Model defining advanced date filters for a dashboard."""
    _name = 'dashboard.date.filter'
    _description = 'Dashboard Advanced Date Filter'
    _order = 'sequence, id'

    name = fields.Char(string='Filter Name', required=True, help='Name of the date filter.')
    sequence = fields.Integer(string='Sequence', default=10, help='Sequence order of the filter.')
    dashboard_menu_id = fields.Many2one(
        'dashboard.menu',
        string='Dashboard',
        required=True,
        ondelete='cascade',
        help='Dashboard this filter applies to.'
    )

    filter_type = fields.Selection([
        ('week', 'Specific Week'),
        ('month', 'Specific Month'),
        ('year', 'Specific Year')
    ], string='Type', default='week', required=True, help='Type of the date filter.')

    year = fields.Integer(
        string='Year',
        default=lambda self: fields.Date.today().year,
        help='Year to filter by.'
    )
    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', default=lambda self: str(fields.Date.today().month), help='Month to filter by.')

    week_number = fields.Selection([
        ('1', 'Week 1'), ('2', 'Week 2'), ('3', 'Week 3'),
        ('4', 'Week 4'), ('5', 'Week 5')
    ], string='Week Number', default='1', help='Week number of the month.')

    day_range_start = fields.Integer(string='Start Day', default=1, help='Start day of the week.')
    day_range_end = fields.Integer(string='End Day', default=7, help='End day of the week.')

    @api.onchange('week_number', 'filter_type')
    def _onchange_week_number(self):
        """Update day range automatically based on selected week number."""
        if self.filter_type == 'week' and self.week_number:
            week_num = int(self.week_number)
            self.day_range_start = (week_num - 1) * 7 + 1
            self.day_range_end = min(week_num * 7, 31)

    @api.constrains('day_range_start', 'day_range_end', 'week_number', 'filter_type')
    def _check_days(self):
        """Ensure day ranges are valid for the selected week."""
        for rec in self:
            if rec.filter_type == 'week':
                week_num = int(rec.week_number)
                min_day = (week_num - 1) * 7 + 1
                max_day = week_num * 7
                # Adjust for Week 5 which might go up to 31
                if week_num == 5:
                    max_day = 31

                if not (min_day <= rec.day_range_start <= max_day) or not (min_day <= rec.day_range_end <= max_day):
                    raise ValidationError(_("For Week {0}, the day range must be between {1} and {2}.").format(week_num, min_day, max_day))

                if rec.day_range_start > rec.day_range_end:
                    raise ValidationError(_("Start day cannot be greater than end day."))
