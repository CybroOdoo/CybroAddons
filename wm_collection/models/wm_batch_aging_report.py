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
from odoo import fields, models


class WmBatchAgingReport(models.Model):
    """Reporting model for Batch Inventory Aging (_auto = False)."""
    _name = 'wm.batch.aging.report'
    _description = 'Batch Inventory Aging'
    _auto = False
    _order = 'age_days desc, batch_id'

    batch_id = fields.Many2one('waste.batch', string='Batch', readonly=True)
    line_id = fields.Many2one('waste.batch.line', string='Batch Line', readonly=True)
    product_id = fields.Many2one('product.product', string='Waste Material', readonly=True)
    category_id = fields.Many2one('wm.waste.category', string='Waste Category', readonly=True)
    hazardous = fields.Boolean(string='Hazardous', readonly=True)
    inspection_state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('failed', 'Failed')
    ], string='Inspection State', readonly=True)

    create_date = fields.Date(string='Creation Date', readonly=True)
    age_days = fields.Integer(string='Age (Days)', readonly=True, aggregator='avg')
    remaining_qty = fields.Float(string='Remaining Qty', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', readonly=True)
    location_id = fields.Many2one('stock.location', string='Location', readonly=True)

    def init(self):
        """ Create or replace SQL view for batch aging analysis. """
        self.env.cr.execute("""
            DROP VIEW IF EXISTS wm_batch_aging_report;
            CREATE OR REPLACE VIEW wm_batch_aging_report AS (
                SELECT
                    l.id AS id,
                    b.id AS batch_id,
                    l.id AS line_id,
                    l.product_id,
                    l.category_id,
                    l.hazardous,
                    b.inspection_state,
                    CAST(COALESCE(b.create_date, NOW()) AS DATE) AS create_date,
                    (CURRENT_DATE - CAST(COALESCE(b.create_date, NOW()) AS DATE)) AS age_days,
                    (l.quantity - COALESCE(l.sorted_qty, 0.0)) AS remaining_qty,
                    b.warehouse_id,
                    b.location_id
                FROM waste_batch_line l
                JOIN waste_batch b ON l.batch_id = b.id
                WHERE (l.quantity - COALESCE(l.sorted_qty, 0.0)) > 0
            )
        """)
