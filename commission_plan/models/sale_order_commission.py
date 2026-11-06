# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class SaleOrderCommission(models.Model):
    """Commission earned by a salesperson on a sale order."""
    _name = 'sale.order.commission'
    _description = 'Sale Order Commission'
    _order = 'order_date desc, id desc'
    _rec_name = 'order_id'

    order_id = fields.Many2one('sale.order', required=True, ondelete='cascade',
                                index=True, string='Sale Order')
    order_date = fields.Datetime(related='order_id.date_order', store=True,
                                 index=True)
    user_id = fields.Many2one('res.users', required=True, index=True,
                              string='Salesperson')
    team_id = fields.Many2one('crm.team', index=True, string='Sales Team')
    commission_id = fields.Many2one('crm.commission', required=True,
                                    string='Commission Plan')
    plan_source = fields.Selection(
        [('team', 'Sales Team Plan'), ('user', 'Salesperson Plan')], required=True, default='team',
        help='Which plan assignment produced commission for this line')
    product_id = fields.Many2one('product.product')
    category_id = fields.Many2one('product.category')
    revenue = fields.Monetary(string='Commissionable Revenue')
    rate = fields.Float(string='Rate (%)')
    amount = fields.Monetary(string='Commission Amount', required=True)
    commission_type = fields.Selection(
        [('earned', 'Earned'), ('return', 'Return')],
        string='Type', default='earned', required=True, index=True,
        help='"Earned" is the commission generated from a paid sale order. '
             '"Return" is a negative record clawing back part of an '
             '"Earned" line because of a credit note against that order.')
    return_move_id = fields.Many2one(
        'account.move', string='Credit Note',
        help='Credit note that caused this return commission line.')
    origin_commission_id = fields.Many2one(
        'sale.order.commission', string='Original Commission',
        help='The "Earned" commission line this return line claws back.')
    currency_id = fields.Many2one(related='order_id.currency_id', store=True,
                                  readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', store=True,
                                 readonly=True)
