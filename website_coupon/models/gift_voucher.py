# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: LINTO C T(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from dateutil import parser

import string
import random

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GiftVoucher(models.Model):
    _name = 'gift.voucher'

    name = fields.Char(string="Name", required=True)
    voucher_type = fields.Selection(
        selection=[
            ('product', 'Product'),
            ('category', 'Product Category'),
            ('all', 'All Products'),
        ], string="Applicable on ", default='product'
    )
    product_id = fields.Many2one('product.product', string="Product")
    product_categ = fields.Many2one('product.category',
                                    string="Product Category")
    min_value = fields.Integer(string="Minimum Voucher Value", required=True)
    max_value = fields.Integer(string="Maximum Voucher Value", required=True)
    expiry_date = fields.Date(string="Expiry Date", required=True)

    def is_order_line_eligible(self, order_line):
        if self.voucher_type == 'product':
            return order_line.product_id == self.product_id
        elif self.voucher_type == 'category':
            return order_line.product_id.categ_id == self.product_categ
        elif self.voucher_type == 'all':
            return True

    @api.multi
    def eligible_lines(self, order):
        self.ensure_one()
        return filter(self.is_order_line_eligible, order.order_line or ())


class GiftCoupon(models.Model):
    _name = 'gift.coupon'

    def get_code(self):
        size = 7
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

    _sql_constraints = [
        ('name_uniq', 'unique (code)', "Code already exists !"),
    ]

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", default=get_code)
    voucher = fields.Many2one('gift.voucher', string="Voucher", required=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    partner_id = fields.Many2one('res.partner',
                                 string="Limit to a Single Partner")
    limit = fields.Integer(string="Total Available For Each User", default=1)
    total_avail = fields.Integer(string="Total Available", default=1)
    voucher_val = fields.Float(string="Voucher Value")
    type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
        ], store=True, default='fixed')

    @api.onchange('voucher_val')
    def check_val(self):
        if (self.voucher_val > self.voucher.max_value
                or self.voucher_val < self.voucher.min_value):
            raise UserError(_("Please check the voucher value"))

    @api.multi
    def amount(self, product_price):
        if self.type == 'fixed':
            return self.voucher_val
        elif self.type == 'percentage':
            return product_price * self.voucher_val / 100.

    @api.multi
    def applied_coupons(self, partner):
        self.ensure_one()
        return self.env['partner.coupon'].sudo().search([
            ('coupon', '=', self.code),
            ('partner_id', '=', partner.id),
            ], limit=1)

    @api.multi
    def available_coupons(self, partner):
        if not self.limit > 0:
            return self.total_avail
        else:
            return min(self.total_avail,
                       self.limit - self.applied_coupons(partner).number or 0)

    @api.multi
    def consume_coupon(self, order):
        """ Consume present coupon as much as possible to reduce given order's
        price, and return a integer number of consumed coupons and a (positive)
        amount.
        """

        # Determine coupon amount from eligible order lines
        eligible_lines = self.voucher.eligible_lines(order)
        if not eligible_lines:
            return 0, 0

        available = self.available_coupons(order.partner_id)

        coupons_used, coupons_amount = 0, 0.
        for line in sorted(eligible_lines, reverse=True,
                           key=lambda l: l.product_id.list_price):
            used_qtty = min(line.product_uom_qty, available)
            if used_qtty:
                coupons_amount += used_qtty * self.amount(
                    line.product_id.list_price)
                coupons_used += used_qtty
                available -= used_qtty

        if coupons_used:
            # update coupon balance
            self.write({'total_avail': self.total_avail - coupons_used})
            # create a record for this partner: he has used this coupon once
            self.use_coupon(order.partner_id, coupons_used)

        return coupons_used, coupons_amount

    @api.multi
    def use_coupon(self, partner, number):
        """ Register given partner usage of the coupon `number` of times
        and adjust the total_avail attribute of the coupon accordingly.
        """
        self.ensure_one()
        applied_coupons = self.applied_coupons(partner)
        if not applied_coupons:
            partner.write({
                'applied_coupon': [(0, 0, {
                    'partner_id': partner.id,
                    'coupon': self.code,
                    'number': number,
                    })]
                })
        else:
            applied_coupons.write(
                {'number': applied_coupons.number + number})
        self.total_avail -= number

    @api.multi
    def is_valid(self, partner):
        self.ensure_one()

        if self.total_avail <= 0:
            return False

        if self.partner_id and self.partner_id != partner:
            return False

        if (self.limit > 0
                and self.applied_coupons(partner).number >= self.limit):
            return False

        today = datetime.now().date()

        if today > parser.parse(self.voucher.expiry_date).date():
            return False

        if self.start_date and today < parser.parse(self.start_date).date():
            return False

        if self.end_date and today > parser.parse(self.end_date).date():
            return False

        return True


class CouponPartner(models.Model):
    _name = 'partner.coupon'

    partner_id = fields.Many2one('res.partner', string="Partner")
    coupon = fields.Char(string="Coupon Applied")
    number = fields.Integer(string="Number of Times Used")


class PartnerExtended(models.Model):
    _inherit = 'res.partner'

    applied_coupon = fields.One2many('partner.coupon', 'partner_id',
                                     string="Coupons Applied")
