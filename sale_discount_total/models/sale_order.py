#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    """Add a global discount, discount approval and the 'Waiting Approval'
    state on sale orders."""
    _inherit = 'sale.order'

    state = fields.Selection(
        selection_add=[('waiting', 'Waiting Approval'), ('sale',)],
        ondelete={'waiting': 'set default'},
    )
    discount_type = fields.Selection(
        [('percent', 'Percentage'), ('amount', 'Amount')],
        default='percent',
        help="Apply the discount as a percentage or as a fixed amount.")
    discount_rate = fields.Float(
        digits=(16, 2),
        help="Discount percentage or amount applied on the order total.")
    amount_discount = fields.Monetary(
        string='Discount', store=True, readonly=True,
        compute='_compute_amount_discount',
        help="Total discount amount of the order lines.")
    margin_test = fields.Float(
        string="Margin (Discount)", compute='_compute_margin_test',
        help="Margin of the order when the Sales Margin app is installed.")

    @api.depends('order_line.product_uom_qty', 'order_line.price_unit',
                 'order_line.discount')
    def _compute_amount_discount(self):
        """Compute the total discount given on the order lines."""
        for order in self:
            order.amount_discount = sum(
                line.product_uom_qty * line.price_unit * line.discount / 100
                for line in order.order_line if not line.display_type)

    @api.depends('amount_untaxed', 'amount_tax', 'amount_total')
    def _compute_margin_test(self):
        """Show the margin when the Sales Margin app is installed."""
        has_margin = 'margin' in self._fields
        for order in self:
            order.margin_test = order.margin if has_margin else 0.0

    def _needs_discount_approval(self):
        """Return True when the average line discount of the order exceeds
        the discount limit of its company."""
        self.ensure_one()
        company = self.company_id
        lines = self.order_line.filtered(lambda line: not line.display_type)
        if (company.so_double_validation != 'two_step'
                or not company.so_double_validation_limit or not lines):
            return False
        discount = sum(lines.mapped('discount')) / len(lines)
        return discount > company.so_double_validation_limit

    def action_confirm(self):
        """Send the orders whose discount exceeds the company limit to
        approval and confirm the others."""
        if self.env.context.get('skip_discount_approval'):
            return super().action_confirm()
        to_approve = self.filtered(lambda order: order._needs_discount_approval())
        to_approve.write({'state': 'waiting'})
        to_confirm = self - to_approve
        if to_confirm:
            return super(SaleOrder, to_confirm).action_confirm()
        return True

    def action_approve(self):
        """Confirm the orders waiting for discount approval."""
        return self.with_context(skip_discount_approval=True).action_confirm()

    def _confirmation_error_message(self):
        """Allow orders waiting for approval to be confirmed and block the
        confirmation of orders having lines without a product."""
        self.ensure_one()
        if self.state not in {'draft', 'sent', 'waiting'}:
            return self.env._(
                "Some orders are not in a state requiring confirmation.")
        if any(not line.display_type and not line.is_downpayment
               and not line.product_id for line in self.order_line):
            return self.env._(
                "Some order lines are missing a product, you need to correct "
                "them before going further.")
        return False

    @api.onchange('discount_type', 'discount_rate', 'order_line')
    def _onchange_discount_rate(self):
        """Apply the global discount on all the order lines."""
        for order in self:
            lines = order.order_line.filtered(
                lambda line: not line.display_type)
            if order.discount_type == 'percent':
                discount = order.discount_rate
            else:
                total = sum(line.product_uom_qty * line.price_unit
                            for line in lines)
                discount = order.discount_rate / total * 100 if total else 0.0
            lines.discount = discount

    def _prepare_invoice(self):
        """Pass the discount type and rate on to the invoice."""
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({
            'discount_type': self.discount_type,
            'discount_rate': self.discount_rate,
        })
        return invoice_vals

    def button_dummy(self):
        """Apply the global discount from the '(update)' button."""
        self._onchange_discount_rate()
        return True
