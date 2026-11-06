# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul (odoo@cybrosys.com)
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


class PriceHistory(models.Model):
    """
    Keep track of the standard price of products as it changes.
    """
    _name = 'price.history'
    _description = 'Products Price History'
    _order = 'datetime desc'

    def _get_default_company_id(self):
        """Returns default company of the user"""
        return self.env.company.id

    company_id = fields.Many2one(
        'res.company', required=True, help="Choose your company",
        default=lambda self: self._get_default_company_id())
    product_id = fields.Many2one('product.product',
                                 ondelete='cascade', required=True,
                                 help="Choose product")
    datetime = fields.Datetime(string='Date', default=fields.Datetime.now,
                               help="Choose the date")
    cost = fields.Float(digits='Product Price',
                        help="Product Price")
