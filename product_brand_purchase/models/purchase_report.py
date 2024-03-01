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


class PurchaseReport(models.Model):
    """Inherit purchase_report to add field brand_id"""
    _inherit = 'purchase.report'

    brand_id = fields.Many2one('product.brand', string='Brand',
                               help='Brand Name')

    def _select(self):
        """Brand in pivot view."""
        res = super(PurchaseReport, self)._select()
        query = res.split('t.categ_id as category_id,', 1)
        res = query[0] + 't.categ_id as category_id,t.brand_id as brand_id,' + \
              query[1]
        return res

    def _group_by(self):
        """Group with brand"""
        res = super(PurchaseReport, self)._group_by()
        query = res.split('t.categ_id,', 1)
        res = query[0] + 't.categ_id,t.brand_id,' + query[1]
        return res
