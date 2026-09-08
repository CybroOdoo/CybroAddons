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


class WmCollectionReport(models.Model):
    """Reporting model for Waste Collection Analysis (_auto = False)."""
    _name = 'wm.collection.report'
    _description = 'Collection Analysis'
    _auto = False
    _order = 'date desc, id desc'

    waste_category_id = fields.Many2one('wm.waste.category', string='Waste Category', readonly=True)
    collection_point_id = fields.Many2one('wm.collection.point', string='Collection Point', readonly=True)
    driver_id = fields.Many2one('res.partner', string='Driver', readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('dispatched', 'Dispatched'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('signed', 'Signed'),
        ('invoiced', 'Invoiced'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    weight_kg = fields.Float(string='Weight (kg)', readonly=True)
    volume_l = fields.Float(string='Volume (L)', readonly=True)
    order_count = fields.Integer(string='Order Count', readonly=True)

    def init(self):
        """ Create or replace the SQL view for collection reporting. """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wm_collection_report AS (
                SELECT
                    min(l.id) AS id,
                    pt.wm_waste_category_id AS waste_category_id,
                    o.collection_point_id AS collection_point_id,
                    o.driver_id AS driver_id,
                    o.vehicle_id AS vehicle_id,
                    o.partner_id AS partner_id,
                    o.state AS state,
                    CAST(COALESCE(o.scheduled_start, o.create_date) AS DATE) AS date,
                    o.company_id AS company_id,
                    SUM(COALESCE(l.weight, 0.0)) AS weight_kg,
                    0.0 AS volume_l,
                    COUNT(DISTINCT o.id) AS order_count
                FROM wm_collection_order_line l
                JOIN wm_collection_order o ON l.order_id = o.id
                LEFT JOIN product_product p ON l.product_id = p.id
                LEFT JOIN product_template pt ON p.product_tmpl_id = pt.id
                GROUP BY
                    pt.wm_waste_category_id,
                    o.collection_point_id,
                    o.driver_id,
                    o.vehicle_id,
                    o.partner_id,
                    o.state,
                    CAST(COALESCE(o.scheduled_start, o.create_date) AS DATE),
                    o.company_id
            )
        """)
