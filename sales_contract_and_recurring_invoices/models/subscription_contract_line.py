# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: K Sai Saran Varma(odoo@cybrosys.com)
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
    price_subtotal = fields.Monetary(
        compute='_compute_amount',
        string='Subtotal',
        store=True,
        precompute=True)  # precompute helps UI responsiveness

    price_total = fields.Monetary(
        compute='_compute_amount',
        string='Total',
        store=True,
        precompute=True)

    # Ensure your legacy field also stores correctly
    sub_total = fields.Monetary(
        string="Total (Legacy)",
        compute='_compute_amount',
        store=True,
        precompute=True)

    @api.depends('product_id')
    def _compute_description(self):
        """ Compute product description """
        for option in self:
            if not option.product_id:
                continue
            product_lang = option.product_id.with_context(
                lang=self.subscription_contract_id.partner_id.lang)
            option.description = product_lang.get_product_multiline_description_sale()

    @api.onchange('product_id')
    def _onchange_product_id_taxes(self):
        """ Automatically fetch taxes when product is selected """
        for rec in self:
            if rec.product_id:
                rec.tax_ids = rec.product_id.taxes_id.filtered(
                    lambda t: t.company_id == rec.subscription_contract_id.company_id
                )

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

    @api.depends('qty_ordered', 'price_unit', 'tax_ids', 'discount')
    def _compute_amount(self):
        for rec in self:
            # 1. Calculate price after discount
            discount_factor = (1 - (rec.discount or 0.0) / 100.0)
            price_after_discount = rec.price_unit * discount_factor

            # 2. Use Odoo's tax engine
            # We pass partner and currency to ensure rounding is correct on Save
            taxes = rec.tax_ids.compute_all(
                price_after_discount,
                rec.currency_id,
                rec.qty_ordered,
                product=rec.product_id,
                partner=rec.subscription_contract_id.partner_id
            )

            # 3. Assigning values - using .get() is safer during the Save process
            rec.price_subtotal = taxes.get('total_excluded', 0.0)
            rec.price_total = taxes.get('total_included', 0.0)
            rec.sub_total = taxes.get('total_excluded', 0.0)