# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
##############################################################################
from odoo import api, fields, models


class SubscriptionContractLines(models.Model):
    """ Add subscription contract line """
    _name = 'subscription.contracts.line'
    _description = 'Subscription Contracts Line'

    subscription_contract_id = fields.Many2one(
        'subscription.contracts',
        string='Subscription Contracts',
        help='Subscription Contract Reference')
    product_id = fields.Many2one('product.product',
                                 string='Products',
                                 help='Products to be added in contract')
    currency_id = fields.Many2one(string='Currency',
                                  related='subscription_contract_id.currency_id',
                                  depends=[
                                      'subscription_contract_id.currency_id'])
    description = fields.Text(
        string="Description", compute='_compute_description', store=True,
        readonly=False, precompute=True, help='Product description')
    qty_ordered = fields.Float(string="Quantity",
                               digits='Product Unit of Measure', default=1.0,
                               help='Ordered Quantity')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure',
                                     compute='_compute_product_uom', store=True,
                                     help='Unit of measure of product')
    price_unit = fields.Float(string="Unit Price",
                              compute='_compute_price_unit',
                              digits='Product Price',
                              store=True, readonly=False, precompute=True,
                              help='Unit price of product')
    tax_ids = fields.Many2many(comodel_name='account.tax', string="Taxes",
                               context={'active_test': False},
                               help='Taxes to be added')
    discount = fields.Float(string="Discount (%)", digits='Discount',
                            store=True, readonly=False, help='Discount in %')
    sub_total = fields.Monetary(
        string="Total", compute='_compute_amount', store=True, precompute=True,
        help='Sub Total Amount')

    @api.depends('product_id')
    def _compute_description(self):
        """ Compute product description """
        for option in self:
            if not option.product_id:
                continue
            product_lang = option.product_id.with_context(
                lang=self.subscription_contract_id.partner_id.lang)
            option.description = product_lang.get_product_multiline_description_sale()

    @api.depends('product_id')
    def _compute_product_uom(self):
        """ Compute product uom """
        for rec in self:
            rec.product_uom_id = rec.product_id.uom_id

    @api.depends('product_id')
    def _compute_price_unit(self):
        """ Compute unit price"""
        for rec in self:
            rec.price_unit = rec.product_id.lst_price

    @api.depends('product_id', 'qty_ordered', 'discount', 'price_unit')
    def _compute_amount(self):
        """ Compute total amount """
        for rec in self:
            total = rec.price_unit * rec.qty_ordered
            discount = total * rec.discount / 100
            rec.sub_total = total - discount
