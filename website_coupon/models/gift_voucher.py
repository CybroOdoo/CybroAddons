# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: LINTO C T(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

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
import string
import random
from odoo import models, fields, api, _
from datetime import datetime,date
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
    product_categ = fields.Many2one('product.category', string="Product Category")
    min_value = fields.Integer(string="Minimum Voucher Value", required=True)
    max_value = fields.Integer(string="Maximum Voucher Value", required=True)
    expiry_date = fields.Date(string="Expiry Date", required=True)


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
    partner_id = fields.Many2one('res.partner', string="Limit to a Single Partner")
    limit = fields.Integer(string="Total Available For Each User", default=1)
    total_avail = fields.Integer(string="Total Available", default=1)
    voucher_val = fields.Float(string="Voucher Value")
    type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
        ], store=True, default='fixed')

    @api.onchange('voucher_val')
    def check_val(self):
        if self.voucher_val > self.voucher.max_value or self.voucher_val < self.voucher.min_value:
            raise UserError(_("Please check the voucher value"))


class CouponPartner(models.Model):
    _name = 'partner.coupon'

    partner_id = fields.Many2one('res.partner', string="Partner")
    coupon = fields.Char(string="Coupon Applied")
    number = fields.Integer(string="Number of Times Used")


class PartnerExtended(models.Model):
    _inherit = 'res.partner'

    applied_coupon = fields.One2many('partner.coupon', 'partner_id', string="Coupons Applied")
