# -*- coding: utf-8 -*-
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
        schedules = self.search([
            ('active', '=', True),
            ('next_run_date', '<=', fields.Datetime.now())
        ])

        for schedule in schedules:
            if schedule.route_id:
                for line in schedule.route_id.line_ids:
                    point = line.collection_point_id
                    if point:
                        self.env['wm.collection.order'].create({
                            'partner_id': point.partner_id.id,
                            'collection_point_id': point.id,
                            'route_id': schedule.route_id.id,
                            'vehicle_id': schedule.route_id.vehicle_id.id if schedule.route_id.vehicle_id else False,
                            'driver_id': schedule.route_id.driver_id.id if schedule.route_id.driver_id else False,
                            'state': 'draft',
                        })

            # Calculate the next run date based on recurrence
            if schedule.recurrence == 'daily':
                schedule.next_run_date += timedelta(days=1)
            elif schedule.recurrence == 'weekly':
                schedule.next_run_date += timedelta(days=7)
            elif schedule.recurrence == 'biweekly':
                schedule.next_run_date += timedelta(days=14)
            elif schedule.recurrence == 'monthly':
                schedule.next_run_date += relativedelta(months=1)
