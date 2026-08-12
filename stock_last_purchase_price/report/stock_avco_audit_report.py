# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, tools


class StockAverageCostReportLast(models.AbstractModel):
    _inherit = 'stock.avco.report'

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'stock_avco_report')
        query = """
    CREATE OR REPLACE VIEW stock_avco_report AS (
    SELECT
        sm.id AS id,
        sm.product_id,
        sm.date,
        picking.user_id,
        sm.company_id,
        sm.reference,
        CASE WHEN sm.is_in THEN sm.value ELSE -sm.value END AS value,
        CASE WHEN sm.is_in THEN sm.quantity ELSE -sm.quantity END AS quantity,
        'stock.move' AS res_model_name,
        'Operation' AS description
    FROM
        stock_move sm
    LEFT JOIN
        stock_picking picking ON sm.picking_id = picking.id
    LEFT JOIN
        product_product pp ON sm.product_id = pp.id
    LEFT JOIN
        product_template pt ON pp.product_tmpl_id = pt.id
    LEFT JOIN
        product_category pc ON pt.categ_id = pc.id
    LEFT JOIN
        res_company company ON sm.company_id = company.id
    WHERE
        sm.state = 'done'
        AND (sm.is_in = TRUE OR sm.is_out = TRUE)
        -- Ignore moves for standard cost method. Only display the list of cost updates
        AND (
            (pt.categ_id IS NOT NULL AND pc.property_cost_method ->> company.id::text IN ('fifo', 'average','last'))
            OR (pt.categ_id IS NULL OR pc.property_cost_method IS NULL AND company.cost_method IN ('fifo', 'average','last'))
        )
    UNION ALL
    SELECT
        -pv.id,
        pv.product_id,
        pv.date,
        pv.user_id,
        pv.company_id,
        'Adjustment' AS reference, -- Set a fixed string for the reference
        pv.value,
        0 AS quantity, -- Set quantity to 0 as requested,
        'product.value' AS res_model_name,
        pv.description
    FROM
        product_value pv
    WHERE
        pv.move_id IS NULL
    );
    """
        self.env.cr.execute(query)
