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


class WmFleetExpiryReport(models.Model):
    """SQL view combining vehicle certificate and licence expiry dates for fleet compliance monitoring."""
    _name = 'wm.fleet.expiry.report'
    _description = 'Certificate & Licence Expiry Report'
    _auto = False
    _order = 'expiry_date asc, id asc'

    entity_type = fields.Selection([
        ('vehicle', 'Vehicle'),
        ('driver', 'Driver')
    ], string='Entity Type', readonly=True)
    entity_name = fields.Char(string='Entity Name', readonly=True)
    document_type = fields.Char(string='Document Type', readonly=True)
    expiry_date = fields.Date(string='Expiry Date', readonly=True)
    days_remaining = fields.Integer(string='Days Remaining', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    def init(self):
        """
        Create or replace SQL view combining vehicle and driver document
        expiries.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wm_fleet_expiry_report AS (
                -- 1. Vehicle Pollution Cert Expiry
                SELECT
                    (v.id * 10 + 1) AS id,
                    'vehicle' AS entity_type,
                    v.name AS entity_name,
                    'Pollution Certificate' AS document_type,
                    v.pollution_cert_expiry AS expiry_date,
                    (v.pollution_cert_expiry - CURRENT_DATE) AS days_remaining,
                    v.company_id AS company_id
                FROM fleet_vehicle v
                WHERE v.pollution_cert_expiry IS NOT NULL

                UNION ALL

                -- 2. Vehicle Fitness Cert Expiry
                SELECT
                    (v.id * 10 + 2) AS id,
                    'vehicle' AS entity_type,
                    v.name AS entity_name,
                    'Fitness Certificate' AS document_type,
                    v.fitness_cert_expiry AS expiry_date,
                    (v.fitness_cert_expiry - CURRENT_DATE) AS days_remaining,
                    v.company_id AS company_id
                FROM fleet_vehicle v
                WHERE v.fitness_cert_expiry IS NOT NULL

                UNION ALL

                -- 3. Vehicle Insurance Expiry
                SELECT
                    (v.id * 10 + 3) AS id,
                    'vehicle' AS entity_type,
                    v.name AS entity_name,
                    'Insurance Policy' AS document_type,
                    v.insurance_expiry AS expiry_date,
                    (v.insurance_expiry - CURRENT_DATE) AS days_remaining,
                    v.company_id AS company_id
                FROM fleet_vehicle v
                WHERE v.insurance_expiry IS NOT NULL

                UNION ALL

                -- 4. Driver Licence Expiry
                SELECT
                    (p.id * 10 + 4) AS id,
                    'driver' AS entity_type,
                    p.name AS entity_name,
                    'Driver Licence' AS document_type,
                    p.licence_expiry AS expiry_date,
                    (p.licence_expiry - CURRENT_DATE) AS days_remaining,
                    p.company_id AS company_id
                FROM res_partner p
                WHERE p.licence_expiry IS NOT NULL
            )
        """)
