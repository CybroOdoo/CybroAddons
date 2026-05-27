# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
"""
Purchase Report module. Enhances purchase report with brand filtering.
"""
from odoo import fields, models
from odoo.tools.sql import SQL

class PurchaseReport(models.Model):
    """Inherit purchase_report to add field brand_id"""
    _inherit = 'purchase.report'

    brand_id = fields.Many2one('product.brand', string='Brand',
                               help='Brand Name')

    def _select(self) -> SQL:
        """Extend the SELECT query to include the brand_id field."""
        return SQL("%s, t.brand_id", super()._select())

    def _group_by(self) -> SQL:
        """Extend the GROUP BY clause to include the brand_id field."""
        return SQL("%s, t.brand_id", super()._group_by())
