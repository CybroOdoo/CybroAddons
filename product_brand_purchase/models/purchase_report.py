# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
"""
Purchase Report module. Enhances purchase report with brand filtering.
"""
from odoo import fields, models
from odoo.tools.sql import SQL
from odoo.models import TableSQL

class PurchaseReport(models.Model):
    """Inherit purchase_report to add field brand_id"""
    _inherit = 'purchase.report'

    brand_id = fields.Many2one('product.brand', string='Brand',
                               help='Brand Name')

    def _select_list(self, table: TableSQL):
        """Extend the SELECT query to include the brand_id field."""
        res = super()._select_list(table)
        res.append(
            SQL("%s AS brand_id", table.product_id.product_tmpl_id.brand_id)
        )
        return res

    def _groupby_list(self, table: TableSQL):
        """Extend the GROUP BY clause to include the brand_id field."""
        res = super()._groupby_list(table)
        res.append(
            table.product_id.product_tmpl_id.brand_id
        )
        return res
