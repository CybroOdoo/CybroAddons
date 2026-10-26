#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class WmSchedule(models.Model):
    """Recurring collection schedule definition for automated collection order generation."""
    _name = 'wm.schedule'
    _description = 'Collection Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', help='Provides information about name', required=True)
    route_id = fields.Many2one(
        'wm.route',
        string='Route',
        domain="[('state', '!=', 'completed')]",
        help='Provides information about route',
        required=True,
    )
    recurrence = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly')
    ], string='Recurrence', required=True, default='weekly')
    next_run_date = fields.Datetime(string='Next Run Date', help='Provides information about next run date')
    active = fields.Boolean(string='Active', help='Provides information about active', default=True)

    @api.model
    def _process_schedules(self):
        """
        Finds due schedules, creates orders for all points in their routes, and
        updates the next_run_date.
        """
        now = fields.Datetime.now()
        schedules = self.search([
            ('active', '=', True),
            ('next_run_date', '<=', now)
        ])

        for schedule in schedules:
            # Catch up in one run: skip occurrences already in the past and
            # only generate the latest due one (instead of one stale batch of
            # orders per hourly cron run).
            run_dt = schedule.next_run_date
            while schedule._get_next_occurrence(run_dt) <= now:
                run_dt = schedule._get_next_occurrence(run_dt)

            if schedule.route_id and schedule.route_id.line_ids:
                route = schedule._get_occurrence_route(run_dt)
                existing_points = route.collection_order_ids.mapped('collection_point_id')
                for line in route.line_ids:
                    point = line.collection_point_id
                    if point and point not in existing_points:
                        self.env['wm.collection.order'].create({
                            'partner_id': point.partner_id.id,
                            'collection_point_id': point.id,
                            'route_id': route.id,
                            'vehicle_id': route.vehicle_id.id if route.vehicle_id else False,
                            'driver_id': route.driver_id.id if route.driver_id else False,
                            'scheduled_start': run_dt,
                            'scheduled_end': run_dt + timedelta(hours=1),
                            'state': 'draft',
                        })

            schedule.next_run_date = schedule._get_next_occurrence(run_dt)

    def _get_next_occurrence(self, run_dt):
        """Return the occurrence following ``run_dt`` for this recurrence."""
        self.ensure_one()
        if self.recurrence == 'daily':
            return run_dt + timedelta(days=1)
        if self.recurrence == 'biweekly':
            return run_dt + timedelta(days=14)
        if self.recurrence == 'monthly':
            return run_dt + relativedelta(months=1)
        return run_dt + timedelta(days=7)

    def _get_occurrence_route(self, run_dt):
        """
        The schedule's route is a template: each occurrence gets its own route
        dated on the occurrence, with the template's stops, vehicle and
        driver. The template itself is reused only while it is still
        unstarted and dated on that day.
        """
        self.ensure_one()
        template = self.route_id
        run_date = fields.Datetime.context_timestamp(self, run_dt).date()
        if template.state == 'to_start' and template.date == run_date:
            return template
        route = template.copy({'date': run_date})
        for line in template.line_ids:
            line.copy({'route_id': route.id})
        return route
