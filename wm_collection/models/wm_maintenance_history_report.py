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


class WmMaintenanceHistoryReport(models.Model):
    """Reporting model for Vehicle Maintenance History (_auto = False)."""
    _name = 'wm.maintenance.history.report'
    _description = 'Maintenance History Report'
    _auto = False
    _order = 'date desc, id desc'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    total_checks = fields.Integer(string='Total Inspection Checks', readonly=True)
    passed_checks = fields.Integer(string='Passed Checks', readonly=True)
    pass_rate = fields.Float(string='Pass Rate (%)', readonly=True)

    def init(self):
        """
        Create or replace SQL view for maintenance history reporting.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wm_maintenance_history_report AS (
                SELECT
                    min(c.id) AS id,
                    c.vehicle_id AS vehicle_id,
                    CAST(COALESCE(c.date, c.create_date) AS DATE) AS date,
                    v.company_id AS company_id,
                    COUNT(c.id) AS total_checks,
                    COUNT(CASE WHEN c.state = 'checked' THEN 1 END) AS passed_checks,
                    CASE
                        WHEN COUNT(c.id) > 0 THEN
                            (COUNT(CASE WHEN c.state = 'checked' THEN 1 END)::float / COUNT(c.id)::float) * 100.0
                        ELSE 0.0
                    END AS pass_rate
                FROM wm_vehicle_maintenance_checklist c
                JOIN fleet_vehicle v ON c.vehicle_id = v.id
                GROUP BY
                    c.vehicle_id,
                    CAST(COALESCE(c.date, c.create_date) AS DATE),
                    v.company_id
            )
        """)
