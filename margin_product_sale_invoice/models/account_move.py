# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cost_price_amount = fields.Float(string='Cost',
                                     compute='compute_cost_price_')
    margin_amount = fields.Float(string='Margin',
                                 compute='compute_margin_amount_',
                                 store=True)

    @api.depends('product_id')
    def compute_cost_price_(self):
        """Compute cost price"""
        self.cost_price_amount = 0
        for record in self:
            if record.product_id:
                record.cost_price_amount = record.product_id.standard_price

    @api.depends('product_id')
    def compute_margin_amount_(self):
        """Compute margin amount"""
        self.margin_amount = 0
        for record in self:
            if record.price_unit and record.cost_price_amount:
                record.margin_amount = record.price_unit - record.cost_price_amount


class AccountMove(models.Model):
    _inherit = 'account.move'

    margin_percent_amount = fields.Float(string='Margin %')
    margin_amount_total = fields.Float(string='Margin Amount')

    def action_post(self):
        """Method for setting the margin amount and margin percent"""
        res = super(AccountMove, self).action_post()
        for record in self:
            if record.invoice_line_ids.product_id:
                record.margin_amount_total = sum(
                    record.invoice_line_ids.mapped('margin_amount'))
                record.margin_percent_amount = record.margin_amount_total / \
                                               record.amount_total * 100
        return res
