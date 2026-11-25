# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class SubscriptionPackageProductLine(models.Model):
    """ Subscription Package Product Line Model """
    _name = 'subscription.package.product.line'
    _description = 'Subscription Package Product Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10,
                              help='Determine the display order')
    subscription_id = fields.Many2one('subscription.package',
                                      string='Subscription',
                                      help='Subscription for the product line')
    res_partner_id = fields.Many2one('res.partner', string='Partner',
                                     help='Subscription partner')
    company_id = fields.Many2one('res.company', string='Company',
                                 related='subscription_id.company_id',
                                 store=True,
                                 help='Subscription Company')
    user_id = fields.Many2one('res.users', string='Salesperson', store=True,
                              related='subscription_id.user_id',
                              help='Add Salesperson')
    product_id = fields.Many2one('product.product', string='Product',
                                 store=True, ondelete='restrict',
                                 domain=[('is_subscription', '=', True)],
                                 help='Choose Product')
    product_qty = fields.Float(string='Quantity', store=True, default=1.0,
                               help='Add Product Quantity')
    product_uom_id = fields.Many2one('uom.uom', string='UoM', store=True,
                                     related='product_id.uom_id',
                                     help='Add Product UOM')

    unit_price = fields.Float(string='Unit Price', store=True, readonly=False,
                              compute='_compute_unit_price', precompute=True,
                              help='Add Product Unit Price')

    @api.depends('product_id')
    def _compute_unit_price(self):
        """ Compute product price from product """
        for line in self:
            if line.product_id:
                line.unit_price = line.product_id.lst_price

    discount = fields.Float(string="Discount (%)", help='Add Discount')
    tax_ids = fields.Many2many('account.tax', string="Taxes",
                               store=True,
                               compute='_compute_tax_ids', readonly=False,
                               help='Add Taxes',
                               domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]")

    @api.depends('product_id', 'company_id')
    def _compute_tax_ids(self):
        """ Compute taxes from product filtered by company """
        for line in self:
            if line.product_id and line.company_id:
                line.tax_ids = line.product_id.taxes_id.filtered(
                    lambda t: t.company_id == line.company_id)
            else:
                line.tax_ids = False
    price_total = fields.Monetary(store=True, readonly=True,
                                  compute='_compute_total_amount',
                                  help='Add Product Price Total')
    price_tax = fields.Monetary(store=True, readonly=True, string='Price Tax',
                                compute='_compute_total_amount',
                                help='Add Price Tax')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  store=True, help='Add Subscription Currency',
                                  related='subscription_id.currency_id')
    total_amount = fields.Monetary(string='Subtotal', store=True,
                                   compute='_compute_total_amount',
                                   help='Add Product Line Subtotal')
    account_move_line_ids = fields.Many2many('account.move.line',
                                             string='Invoiced Lines',
                                             help='Add Invoiced lines')
    qty_invoiced = fields.Float(string='Invoiced Quantity',
                                help='Add Invoiced Quantity')

    @api.depends('product_qty', 'discount', 'unit_price', 'tax_ids')
    def _compute_total_amount(self):
        """ Calculate subtotal amount of product line """
        for line in self:
            price = line.unit_price * (1 - (line.discount or 0.0) / 100.0)
            currency = line.currency_id or line.subscription_id.currency_id or self.env.company.currency_id
            partner = line.subscription_id.partner_id
            taxes = line.tax_ids.compute_all(price,
                                             currency,
                                             line.product_qty,
                                             product=line.product_id,
                                             partner=partner)
            line.price_tax = sum(
                t.get('amount', 0.0) for t in taxes.get('taxes', []))
            line.price_total = taxes.get('total_included', 0.0)
            line.total_amount = taxes.get('total_excluded', 0.0)