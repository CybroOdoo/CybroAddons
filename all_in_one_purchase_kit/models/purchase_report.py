# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class PurchaseReport(models.Model):
    """Inherit model to add fields and methods"""
    _inherit = 'purchase.report'

    brand_id = fields.Many2one(
        'product.brand', string='Brand', help='Select brand of the product'
    )

    def _select(self):
        """Add filter in pivot view"""
        res = super(PurchaseReport, self)._select()
        query = res.split('t.categ_id as category_id,', 1)
        res = query[0] + 't.categ_id as category_id,t.brand_id' \
                          ' as brand_id,' + query[1]
        return res

    def _group_by(self):
        """Add the group by in pivot view"""
        res = super(PurchaseReport, self)._group_by()
        query = res.split('t.categ_id,', 1)
        res = query[0] + 't.categ_id,t.brand_id,' + query[1]
        return res
