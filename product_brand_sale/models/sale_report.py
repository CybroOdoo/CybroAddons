# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class SaleReport(models.Model):
    """
    Inherit sale_report model
    """
    _inherit = 'sale.report'

    brand_id = fields.Many2one('product.brand', string='Brand', help="Brand")

    def _select_additional_fields(self):
        """
        Brand in pivot view of the sale order report
        """
        res = super()._select_additional_fields()
        res['brand_id'] = "t.brand_id"
        return res

    def _group_by_sale(self):
        """
        Brand as filter in the pivot view
        """
        res = super()._group_by_sale()
        res += """,
            t.brand_id"""
        return res
