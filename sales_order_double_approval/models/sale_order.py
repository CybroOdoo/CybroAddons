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
from odoo import _, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """Inherit sale.order to add a manager-approval step."""
    _inherit = 'sale.order'

    state = fields.Selection(
        selection_add=[('to_approve', 'To Approve'), ('sent',)],
        ondelete={'to_approve': 'set default'})

    def _needs_approval(self):
        """Return True if this single order must wait for manager approval."""
        self.ensure_one()
        if self.state not in {'draft', 'sent'}:
            return False
        if self.env.context.get('skip_double_approval'):
            return False
        if not self.company_id.so_double_validation:
            return False
        config = self.env['ir.config_parameter'].sudo()
        if self.env.user.has_group('sales_team.group_sale_manager'):
            return False
        min_amount = config.get_float(
            'sales_order_double_approval.so_min_amount', default=0.0)
        currency_id = config.get_int(
            'sales_order_double_approval.so_min_amount_currency_id',
            default=self.env.ref('base.main_company').currency_id.id,
        )
        threshold_currency = self.env['res.currency'].browse(currency_id).exists()
        if not threshold_currency:
            threshold_currency = self.env.ref('base.main_company').currency_id
        order_date = self.date_order or fields.Date.today()
        amount = self.currency_id._convert(
            self.amount_total, self.company_id.currency_id,
            self.company_id, order_date)
        company_threshold = threshold_currency._convert(
            min_amount, self.company_id.currency_id, self.company_id, order_date)
        return amount > company_threshold

    def button_approve(self):
        """Manager approval: run the real confirmation flow."""
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise UserError(_("Only Sales Managers can approve orders."))
        orders = self.filtered(lambda o: o.state == 'to_approve')
        orders.write({'state': 'draft'})
        return orders.with_context(skip_double_approval=True).action_confirm()

    def action_confirm(self):
        """Orders above the threshold go to 'to_approve' without triggering
        the standard confirmation side effects until a manager approves."""
        to_approve = self.filtered(lambda o: o._needs_approval())
        if to_approve:
            to_approve.write({'state': 'to_approve'})
        self = self - to_approve
        return super().action_confirm()
