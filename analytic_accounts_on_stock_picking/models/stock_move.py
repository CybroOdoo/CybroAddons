# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, api


class StockMove(models.Model):
    """Inherit stock.move to show analytic distribution
    coming from sale or purchase order lines
    """
    _inherit = 'stock.move'

    analytic = fields.Json(
        string='Analytic',
        compute='_compute_analytic',
        help='Analytic Distribution'
    )

    analytic_precision = fields.Integer(
        store=False,
        help='Define the precision of percentage decimal value',
        default=lambda self: self.env['decimal.precision'].precision_get(
            "Percentage Analytic"
        )
    )

    @api.depends(
        'sale_line_id',
        'sale_line_id.analytic_distribution',
        'sale_line_id.order_id.analytic_account_id',
        'purchase_line_id',
        'purchase_line_id.analytic_distribution',
    )
    def _compute_analytic(self):
        for rec in self:
            # ✅ ALWAYS assign a default value
            rec.analytic = False

            # -------- Sale Order Case --------
            if rec.sale_line_id:
                analytic_distribution = (
                    rec.sale_line_id.analytic_distribution or {}
                )

                analytic_account = rec.sale_line_id.order_id.analytic_account_id
                if analytic_account:
                    # copy to avoid mutating cached value
                    analytic_distribution = dict(analytic_distribution)
                    analytic_distribution[str(analytic_account.id)] = 100

                rec.analytic = analytic_distribution

            # -------- Purchase Order Case --------
            elif rec.purchase_line_id:
                rec.analytic = (
                    rec.purchase_line_id.analytic_distribution or False
                )
