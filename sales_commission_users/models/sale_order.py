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
#############################################################################
from odoo import Command, fields, models


class SaleOrder(models.Model):
    """Inherits Sale order model for adding sales commission."""
    _inherit = 'sale.order'

    commission_ids = fields.One2many(
        'commission.lines',
        'sale_order_id',
        string='Sales Commission',
        help="Commission lines generated for this sale order.",
    )

    def action_confirm(self):
        """Add commission lines when a sale order is confirmed."""
        res = super().action_confirm()
        for order in self:
            order.commission_ids.filtered(
                lambda c: c.state != 'invoiced'
            ).unlink()
            commissions = self.env['sales.commission'].search(
                [('sales_person_ids', 'in', order.user_id.id)]
            )
            for com in commissions:
                commission_amount = 0.0
                description = ''
                if com.commission_type == 'standard':
                    description = 'Sales Commission - Standard'
                    commission_amount = (
                        order.amount_total * com.std_commission_perc / 100
                    )
                elif com.commission_type == 'partner_based':
                    description = 'Sales Commission - Partner based'
                    if order.partner_id.affiliated:
                        commission_amount = (
                            order.amount_total
                            * com.affiliated_commission_perc / 100
                        )
                    else:
                        commission_amount = (
                            order.amount_total
                            * com.non_affiliated_commission_perc / 100
                        )
                elif com.commission_type == 'product_based':
                    for rec in com.product_based_ids:
                        matching_lines = order.order_line.filtered(
                            lambda p: p.product_id == rec.product_id
                        )
                        if matching_lines:
                            description = 'Sales Commission - Product Based'
                            for line in matching_lines:
                                commission_amount += (
                                    line.product_id.list_price
                                    * rec.commission / 100
                                )
                elif com.commission_type == 'discount_based':
                    for rec in com.discount_based_ids:
                        matching_lines = order.order_line.filtered(
                            lambda p: p.discount >= rec.discount
                        )
                        if matching_lines:
                            description = 'Sales Commission - Discount Based'
                            commission_amount += (
                                order.amount_total * rec.commission / 100
                            )
                if description and commission_amount:
                    order.commission_ids = [Command.create({
                        'date': order.date_order,
                        'description': description,
                        'sales_person_id': order.user_id.id,
                        'order_ref': order.name,
                        'partner_id': order.partner_id.id,
                        'commission': com.name,
                        'commission_type': com.commission_type,
                        'commission_amount': commission_amount,
                    })]
        return res
