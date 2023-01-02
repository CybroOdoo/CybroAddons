# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

"""inherited account move"""


from odoo import api, models, fields


class AccountMove(models.Model):
    """inherited account move"""
    _inherit = "account.move"

    margin_amount = fields.Float(string='Margin Amount',
                                 compute='_compute_margin',
                                 digits='Product Price')
    margin_percentage = fields.Float(string='Margin Percentage',
                                     compute='_compute_margin',
                                     digits='Product Price')

    @api.depends('invoice_line_ids', 'invoice_line_ids.quantity',
                 'invoice_line_ids.price_unit', 'invoice_line_ids.discount')
    def _compute_margin(self):
        """method for computing margin"""
        line_cost = lines_margin_amount = lines_sale_price = 0.0
        for move in self:
            move.margin_amount = False
            move.margin_percentage = False
            if move.invoice_line_ids:
                for line in move.invoice_line_ids:
                    sale_price = line.price_unit * line.quantity
                    lines_sale_price += sale_price
                    discount = (sale_price * line.discount) / 100
                    cost = line.product_id.standard_price * line.quantity
                    line_cost += cost
                    line_margin_amount = (sale_price - discount) - cost
                    lines_margin_amount += line_margin_amount
                if line_cost:
                    move.margin_amount = lines_margin_amount
                    if lines_sale_price != 0:
                        move.margin_percentage = \
                            lines_margin_amount / lines_sale_price
                else:
                    move.margin_amount = lines_margin_amount
                    move.margin_percentage = 1


class AccountMoveLine(models.Model):
    """inherited account move line"""
    _inherit = 'account.move.line'

    margin_amount = fields.Float(string='Margin Amount', store=True,
                                 compute='_compute_margin',
                                 digits='Product Price')
    margin_percentage = fields.Float(string='Margin Percentage',
                                     compute='_compute_margin', store=True,
                                     digits='Product Price')

    @api.depends('quantity', 'price_unit', 'discount')
    def _compute_margin(self):
        """method for computing margin"""
        for line in self:
            line.margin_amount = False
            line.margin_percentage = False
            if line.product_id:
                sale_price = line.price_unit * line.quantity
                discount = (sale_price*line.discount)/100
                cost = line.product_id.standard_price * line.quantity
                margin_amount = (sale_price - discount) - cost
                if cost:
                    line.margin_amount = margin_amount
                    if sale_price !=0:
                        line.margin_percentage = margin_amount / sale_price
                else:
                    line.margin_amount = margin_amount
                    line.margin_percentage = 1
