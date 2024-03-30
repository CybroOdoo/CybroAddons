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


class CommissionProduct(models.Model):
    """
    This class represents Commission Product Wise.

    This model is used to define commission rates and maximum commission amounts
    for different products.
    """
    _name = 'commission.product'
    _description = 'Commission Product Wise'

    user_id = fields.Many2one('res.users')
    category_id = fields.Many2one('product.category', string='Product Category',
                                  help="Category of the product")
    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('categ_id', '=', category_id)]",
                                 help="Product")
    percentage = fields.Float(string='Rate in Percentage (%)',
                              help="Rate in percentage")
    amount = fields.Monetary(string='Maximum Commission Amount', default=0.0,
                             help="Maximum Commission Amount")
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id,
                                  help="Currency")
    commission_id = fields.Many2one("crm.commission",
                                    string="Commission", help="Commission")
