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
from odoo import fields, models, tools


class WmRouteEfficiencyReport(models.Model):
    """Reporting model for Route Efficiency (_auto = False)."""
    _name = 'wm.route.efficiency.report'
    _description = 'Route Efficiency'
    _auto = False
    _order = 'date desc, id desc'

    route_id = fields.Many2one('wm.route', string='Route', readonly=True)
    driver_id = fields.Many2one('res.partner', string='Driver', readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    distance_km = fields.Float(string='Distance (km)', readonly=True)
    estimated_mins = fields.Float(string='Estimated Mins', readonly=True)
    points_planned = fields.Integer(string='Points Planned', readonly=True)
    orders_completed = fields.Integer(string='Orders Completed', readonly=True)
    completion_rate = fields.Float(string='Completion Rate (%)', readonly=True)

    def init(self):
        """
        Create or replace SQL view for route efficiency analysis.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wm_route_efficiency_report AS (
                SELECT
                    r.id AS id,
                    r.id AS route_id,
                    r.driver_id AS driver_id,
                    r.vehicle_id AS vehicle_id,
                    CAST(COALESCE(r.date, r.create_date) AS DATE) AS date,
                    MAX(o.company_id) AS company_id,
                    0.0 AS distance_km,
                    COALESCE(r.estimated_duration * 60.0, 0.0) AS estimated_mins,
                    COUNT(DISTINCT rl.id) AS points_planned,
                    COUNT(DISTINCT CASE WHEN o.state IN ('completed', 'signed', 'invoiced') THEN o.id END) AS orders_completed,
                    CASE
                        WHEN COUNT(DISTINCT rl.id) > 0 THEN
                            (COUNT(DISTINCT CASE WHEN o.state IN ('completed', 'signed', 'invoiced') THEN o.id END)::float / COUNT(DISTINCT rl.id)::float) * 100.0
                        ELSE 0.0
                    END AS completion_rate
                FROM wm_route r
                LEFT JOIN wm_route_line rl ON rl.route_id = r.id
                LEFT JOIN wm_collection_order o ON o.route_id = r.id
                GROUP BY
                    r.id,
                    r.driver_id,
                    r.vehicle_id,
                    CAST(COALESCE(r.date, r.create_date) AS DATE),
                    r.estimated_duration
            )
        """)
