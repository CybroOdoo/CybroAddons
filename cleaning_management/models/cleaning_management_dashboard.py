# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Safa KB (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models
from odoo.tools import date_utils

BOOKING_STAGES = ['draft', 'booked', 'cleaned', 'cancelled']
QUALITY_STAGES = ['cleaned', 'dirty']


class CleaningManagementDashBoard(models.AbstractModel):
    """Creating new model to extract counts for bookings, cleanings,
    and dirty states, intended for visualization on a dashboard."""
    _name = "cleaning.management.dashboard"
    _description = "Cleaning Management Dashboard"

    def get_dashboard_count(self):
        """Getting count of bookings,teams,cleaning and dirty count"""
        inspection = self.env['cleaning.inspection']
        return {
            'bookings': self.env['cleaning.booking'].search_count([
                ('state', '=', 'booked')]),
            'teams': self.env['cleaning.team'].search_count([]),
            'cleaned': inspection.search_count([('state', '=', 'cleaned')]),
            'dirty': inspection.search_count([('state', '=', 'dirty')]),
        }

    def _booking_period(self, period):
        """Booking counts per state for the current year, quarter,
        month or week. The key names are the ones the dashboard JS reads."""
        today = fields.Date.today()
        counts = dict(self.env['cleaning.booking']._read_group(
            [('booking_date', '>=', date_utils.start_of(today, period)),
             ('booking_date', '<=', date_utils.end_of(today, period))],
            ['state'], ['__count']))
        return {
            f'total_booking_stage_{period}': [stage.capitalize() for stage in BOOKING_STAGES],
            f'total_booking_stage_draft_{period}': counts.get('draft', 0),
            f'total_booking_stage_booked_{period}': counts.get('booked', 0),
            f'total_booking_stage_cleaned_{period}': counts.get('cleaned', 0),
            f'total_booking_stage_canceled_{period}': counts.get(
                'cancelled', 0),
        }

    def _quality_period(self, period):
        """Inspection results (cleaned / dirty) for the current period."""
        now = fields.Datetime.now()
        counts = dict(self.env['cleaning.inspection']._read_group(
            [('inspection_date_and_time', '>=',
              date_utils.start_of(now, period)),
             ('inspection_date_and_time', '<=',
              date_utils.end_of(now, period))],
            ['state'], ['__count']))
        return {
            f'quality_{period}': [stage.capitalize() for stage in QUALITY_STAGES],
            f'cleaned_quality_{period}': counts.get('cleaned', 0),
            f'dirty_quality_{period}': counts.get('dirty', 0),
        }

    def get_the_booking_year(self):
        """Get year wise booking"""
        return self._booking_period('year')

    def get_the_booking_month(self):
        """Get month wise booking"""
        return self._booking_period('month')

    def get_the_booking_week(self):
        """Get week wise booking"""
        return self._booking_period('week')

    def get_the_booking_quarter(self):
        """Get quarter wise booking"""
        return self._booking_period('quarter')

    def quality_year(self):
        """Get year wise quality of cleaning"""
        return self._quality_period('year')

    def quality_month(self):
        """Get month wise quality of cleaning"""
        return self._quality_period('month')

    def quality_week(self):
        """Get week wise quality of cleaning"""
        return self._quality_period('week')

    def quality_quarter(self):
        """Get quarter wise quality of cleaning"""
        return self._quality_period('quarter')

    def cleaning_count(self):
        """Creating a function to retrieve the counts of bookings,
        cleanings, and dirty states."""
        return {
            'bookings': list(self.env['cleaning.booking'].search([])),  # pylint: disable=no-search-all
            'inspections': list(self.env['cleaning.inspection'].search([])),  # pylint: disable=no-search-all
        }