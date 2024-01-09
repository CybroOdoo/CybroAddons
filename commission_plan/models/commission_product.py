# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#     Author: Abhin K(odoo@cybrosys.com)
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
from odoo import api, fields, models


class CommissionProduct(models.Model):
    """commission.product model is defined here"""
    _name = 'commission.product'
    _description = 'Commission Product Wise'

    user_id = fields.Many2one('res.users', string='User',
                              help='Select the User')
    category_id = fields.Many2one('product.category',
                                  string='Product Category',
                                  help='Select the Product Category')
    category_ids = fields.Many2many('product.category',
                                    string='Product Category Reference',
                                    help="To set the domain for the "
                                         "category_id",
                                    compute="_onchange_category_id")
    product_id = fields.Many2one('product.product', string='Product',
                                 help='Select the product')
    commission_amount_type = fields.Selection([('percentage', 'Percentage'),
                                               ('fixed', 'Fixed Amount')],
                                              string="Amount Type",
                                              default='percentage',
                                              help='Commission amount type')
    fixed_amount = fields.Monetary('Commission Amount', default=0.0,
                                   help='Fixed Commission Amount')
    percentage = fields.Float(string='Rate in Percentage (%)',
                              help='Rate in percentage')
    amount = fields.Monetary('Maximum Commission Amount', default=0.0,
                             help='Maximum Commission Amount')
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id,
                                  help='Currency of the company')
    commission_id = fields.Many2one("crm.commission", string='Commission',
                                    help='Select The Crm Commission')

    @api.depends('category_id')
    def _onchange_category_id(self):
        """Function Sets the domain for selected category and removes
        the product if the product is not in the selected category"""
        for rec in self:
            rec.category_ids = rec.category_id.search(
                [('id', 'child_of', rec.category_id.ids)]).ids
            rec.product_id = None if rec.product_id.id not in self.env[
                'product.product'].search(
                [('categ_id', 'in',
                  rec.category_ids.ids)]).ids else rec.product_id.id
