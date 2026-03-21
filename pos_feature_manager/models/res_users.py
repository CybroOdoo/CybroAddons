# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP (Contact : odoo@cybrosys.com)
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

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    pos_allow_numpad = fields.Boolean(
        string='Allow Numpad',
        default=True,
        help='Allow this user to use the numeric keypad in POS.'
    )
    pos_allow_payments = fields.Boolean(
        string='Allow Payments',
        default=True,
        help='Allow this user to process payments in POS.'
    )
    pos_allow_discount = fields.Boolean(
        string='Allow Discount',
        default=True,
        help='Allow this user to apply discounts in POS.'
    )
    pos_allow_qty = fields.Boolean(
        string='Allow Qty',
        default=True,
        help='Allow this user to change product quantities in POS.'
    )
    pos_allow_price_edit = fields.Boolean(
        string='Allow Edit Price',
        default=True,
        help='Allow this user to manually edit product prices in POS.'
    )
    pos_allow_remove_order_line = fields.Boolean(
        string='Allow Remove Order Line',
        default=True,
        help='Allow this user to remove order lines in POS.'
    )
    pos_allow_customer_selection = fields.Boolean(
        string='Allow Customer Selection',
        default=True,
        help='Allow this user to select or add customers in POS.'
    )
    pos_allow_plus_minus = fields.Boolean(
        string='Allow +/- Button',
        default=True,
        help='Allow this user to use the +/- button in POS.'
    )