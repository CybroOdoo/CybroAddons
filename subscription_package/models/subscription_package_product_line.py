# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: JANISH BABU (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, models, fields


class SubscriptionPackageProductLine(models.Model):
    """Subscription Package Product Line Model"""
    _name = 'subscription.package.product.line'
    _description = 'Subscription Package Product Lines'

    subscription_id = fields.Many2one('subscription.package', store=True,
                                      string='Subscription',
                                      help='Choose Subscription Package')
    company_id = fields.Many2one('res.company', string='Company', store=True,
                                 related='subscription_id.company_id')
    create_date = fields.Datetime(string='Create date', store=True,
                                  default=fields.Datetime.now,
                                  help='Add Create Date')
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
                                     ondelete='restrict',
                                     help='Add Product UOM')
    uom_catg_id = fields.Many2one('uom.category', string='UoM Category',
                                  store=True,
                                  related='product_id.uom_id.category_id',
                                  help='Choose Product Uom quantity')
    unit_price = fields.Float(string='Unit Price', store=True, readonly=False,
                              related='product_id.list_price',
                              help='Add Product Unit Price')
    discount = fields.Float(string="Discount (%)", help='Add Discount')
    tax_ids = fields.Many2many('account.tax', string="Taxes",
                               ondelete='restrict',
                               related='product_id.taxes_id', readonly=False,
                               help='Add Taxes')
    price_total = fields.Monetary(store=True, readonly=True,
                                  help='Add Product Price Total')
    price_tax = fields.Monetary(store=True, readonly=True, string='Price Tax',
                                help='Add Price Tax')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  store=True, help='Add Subscription Currency',
                                  related='subscription_id.currency_id')
    total_amount = fields.Monetary(string='Subtotal', store=True,
                                   help='Add Total Amount',
                                   compute='_compute_total_amount')
    sequence = fields.Integer('Sequence', help="Determine the display order",
                              index=True)
    res_partner_id = fields.Many2one('res.partner', string='Partner',
                                     store=True, help='Choose the  Partner',
                                     related='subscription_id.partner_id')

    @api.depends('product_qty', 'unit_price', 'discount', 'tax_ids',
                 'currency_id')
    def _compute_total_amount(self):
        """ Calculate subtotal amount of product line """
        for line in self:
            price = line.unit_price * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_ids._origin.compute_all(price,
                                                     line.subscription_id._origin.currency_id,
                                                     line.product_qty,
                                                     product=line.product_id,
                                                     partner=line.subscription_id._origin.partner_id)
            line.write({
                'price_tax': sum(
                    t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'total_amount': taxes['total_excluded'],
            })

    def _valid_field_parameter(self, field, name):
        if name == 'ondelete':
            return True
        return super(SubscriptionPackageProductLine,
                     self)._valid_field_parameter(field, name)
