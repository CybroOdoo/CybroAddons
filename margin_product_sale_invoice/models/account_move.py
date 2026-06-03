# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    """This class extends for margin on the invoice line"""
    _inherit = 'account.move.line'

    cost_price_amount = fields.Float(string='Cost',
                                     compute='compute_cost_price_amount',
                                     store=True, help='Field for the cost')
    margin_amount = fields.Float(string='Margin Amount',
                                 compute='compute_margin_amount',
                                 store=True,
                                 help='Field displays computed margin')

    @api.depends('product_id', 'price_unit', 'quantity', 'cost_price_amount')
    def compute_margin_amount(self):
        """Compute margin amount"""
        for record in self:
            if record.price_unit and record.cost_price_amount:
                record.margin_amount = (record.price_unit - record.cost_price_amount) * record.quantity
            else:
                record.margin_amount = 0

    @api.depends('product_id', 'currency_id')
    def compute_cost_price_amount(self):
        """Compute cost price amount for the invoice line."""
        for record in self:
            if record.product_id:
                cost = record.product_id.standard_price
                converted_amount = record.env.company.currency_id._convert(
                    from_amount=cost,
                    to_currency=record.currency_id, company=record.company_id,
                    date=fields.Date.today()
                )
                record.cost_price_amount = converted_amount
            else:
                record.cost_price_amount = 0


class AccountMove(models.Model):
    """This class extends for margin on the invoices"""
    _inherit = 'account.move'

    margin_percent_amount = fields.Float(string='Margin %', compute='_compute_margin_info',
                                         store=True, help='Field margin amount in percentage')
    margin_amount_total = fields.Float(string='Margin Amount', compute='_compute_margin_info',
                                       store=True, help='Field displays total margin amount')

    @api.depends('invoice_line_ids.margin_amount', 'amount_total')
    def _compute_margin_info(self):
        """Compute margin percent and amount for the invoice."""
        for record in self:
            total_margin = sum(record.invoice_line_ids.mapped('margin_amount'))
            record.margin_amount_total = total_margin
            if record.amount_total:
                record.margin_percent_amount = total_margin / record.amount_total
            else:
                record.margin_percent_amount = 0
