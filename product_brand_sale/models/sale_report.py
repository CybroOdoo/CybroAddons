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
from odoo import fields, models


class SaleReport(models.Model):
    """
    Inherit sale_report model
    """
    _inherit = 'sale.report'

    brand_id = fields.Many2one('product.brand', string='Brand', help="Brand")

    def _select_dict(self, table):
        """
        Brand in pivot view of the sale order report
        """
        res = super()._select_dict(table)
        res['brand_id'] = table.product_id.product_tmpl_id.brand_id
        return res

    def _groupby_list(self, table):
        """
        Brand as filter in the pivot view
        """
        res = super()._groupby_list(table)
        res.append(table.product_id.product_tmpl_id.brand_id)
        return res
