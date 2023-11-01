# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models
from odoo.addons import decimal_precision as dp


class PriceHistory(models.Model):
    """
    Keep track of the price of products standard prices as they are changed.
    """
    _name = 'price.history'
    _description = 'Products Price History'
    _order = 'datetime desc'

    def _get_default_company_id(self):
        """Returns default company of the user"""
        return self._context.get('force_company', self.env.user.company_id.id)

    company_id = fields.Many2one('res.company', string='Company',
                                 default=_get_default_company_id,
                                 required=True, help="Choose your company")
    product_id = fields.Many2one('product.product', string='Product',
                                 ondelete='cascade', required=True,
                                 help="Choose product")
    datetime = fields.Datetime(string='Date', default=fields.Datetime.now,
                               help="Choose the date")
    cost = fields.Float(string='Cost', digits=dp.get_precision('Product Price'),
                        help="Product Price")
