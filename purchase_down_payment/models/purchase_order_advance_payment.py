# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#
################################################################################
"""Wizard for creating purchase order advance payment bills."""
import time
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command


    # pylint: disable=unknown-option-value,no-wizard-in-models,too-few-public-methods
class PurchaseOrderAdvancePayment(models.TransientModel):
    """Wizard to create down payment bills from purchase orders."""

    # pylint: disable=protected-access
    _name = 'purchase.order.advance.payment'
    _description = 'Purchase Order Advance Payment Bill'

    @api.model
    def _default_product_id(self):
        """Fetch the default down payment product from config parameters."""
        product_id = self.env['ir.config_parameter'].sudo().get_int(
            'purchase_down_payment.po_deposit_default_product_id'
        )
        if product_id:
            return self.env['product.product'].browse(product_id).exists()
        return False

    @api.model
    def _default_currency_id(self):
        """Fetch currency_id from active purchase order."""
        if (
            self.env.context.get('active_model') == 'purchase.order'
            and self.env.context.get('active_id')
        ):
            purchase_order = self.env['purchase.order'].browse(
                self.env.context.get('active_id')
            )
            return purchase_order.currency_id
        return False

    @api.model
    def _default_has_down_payment(self):
        """Check whether active purchase order has down payments."""
        if (
            self.env.context.get('active_model') == 'purchase.order'
            and self.env.context.get('active_id')
        ):
            purchase_order = self.env['purchase.order'].browse(
                self.env.context.get('active_id')
            )
            return bool(purchase_order.order_line.filtered(
                lambda line: line.is_downpayment
            ))
        return False

    advance_payment_method = fields.Selection([
        ('delivered', 'Regular bill'),
        ('percentage', 'Down payment (percentage)'),
        ('fixed', 'Down payment (fixed amount)')
    ], string='Create Bill', default='delivered', required=True,
        help="A standard bill is issued with all the order lines ready "
             "for billing, according to their billing policy.")
    has_down_payments = fields.Boolean(
        string='Has down payments',
        default=lambda self: self._default_has_down_payment(),
        readonly=True,
        help='Indicates whether purchase order already has down payments.',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Down Payment Product',
        domain=[('type', '=', 'service')],
        default=lambda self: self._default_product_id(),
        help='Product used for down payment bills.',
    )
    deduct_down_payments = fields.Boolean(
        string='Deduct down payments',
        default=False,
        help='Deduct existing down payments on subsequent bills.',
    )
    amount = fields.Float(
        string='Down Payment Amount',
        digits='Account',
        help="The percentage of amount to be billed in advance.",
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self._default_currency_id(),
        help='Currency used for down payment.',
    )
    fixed_amount = fields.Monetary(
        string='Down Payment Amount (Fixed)',
        help="The fixed amount to be billed in advance.",
    )
    deposit_account_id = fields.Many2one(
        'account.account',
        string="Income Account",
        domain=[('deprecated', '=', False)],
        help="Account used for deposits.",
    )
    deposit_taxes_ids = fields.Many2many(
        'account.tax',
        string="Vendor Taxes",
        domain=[('type_tax_use', '=', 'purchase')],
        help="Taxes used for deposits.",
    )

    def _get_advance_details(self, order):
        """Calculate down payment amount and label for the order."""
        if self.advance_payment_method == 'percentage':
            if all(self.product_id.supplier_taxes_id.mapped('price_include')):
                amount = order.amount_total * self.amount / 100
            else:
                amount = order.amount_untaxed * self.amount / 100
            name = self.env._(
                "Down payment of %(amount)s%%",
                amount=self.amount,
            )
        else:
            amount = self.fixed_amount
            name = self.env._('Down Payment')
        return amount, name

    def _prepare_po_line(self, order, tax_ids, amount):
        """Prepare values for purchase order down payment line."""
        name = self.env._(
            "Down Payment: %(date)s / %(order)s",
            date=time.strftime('%m-%Y-%d'),
            order=order.name,
        )
        return {
            'name': name,
            'price_unit': amount,
            'product_uom_qty': 0.0,
            'product_qty': 0.0,
            'order_id': order.id,
            'uom_id': self.product_id.uom_id.id,
            'product_id': self.product_id.id,
            'tax_ids': [Command.set(tax_ids)],
            'is_downpayment': True,
            'sequence': (
                order.order_line and order.order_line[-1].sequence + 1 or 10
            ),
            'date_planned': datetime.today(),
        }

    def _prepare_invoice_values(self, order, name, amount, po_line):
        """Prepare vendor bill values for down payment."""
        return {
            'ref': order.partner_ref or '',
            'move_type': 'in_invoice',
            'invoice_origin': order.name,
            'invoice_user_id': order.user_id.id,
            'narration': order.note,
            'partner_id': order.partner_id.id,
            'fiscal_position_id': (
                order.fiscal_position_id
                or order.fiscal_position_id._get_fiscal_position(
                    order.partner_id
                )
            ).id,
            'currency_id': order.currency_id.id,
            'payment_reference': order.partner_ref or '',
            'invoice_payment_term_id': order.payment_term_id.id,
            'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            'invoice_line_ids': [Command.create({
                'name': name,
                'price_unit': amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'purchase_line_id': po_line.id,
                'product_uom_id': po_line.uom_id.id,
            })],
        }

    def _create_bill(self, order, po_line, amount):
        """Create vendor bill for down payment."""
        if (
            self.advance_payment_method == 'percentage' and self.amount <= 0.0
        ) or (
            self.advance_payment_method == 'fixed' and self.fixed_amount <= 0.0
        ):
            raise UserError(
                self.env._(
                    'The value of the down payment amount must be positive.'
                )
            )
        amount, name = self._get_advance_details(order)
        invoice_vals = self._prepare_invoice_values(
            order, name, amount, po_line
        )
        if order.fiscal_position_id:
            invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id
        return self.env['account.move'].with_company(
            order.company_id
        ).sudo().create(invoice_vals).with_user(self.env.uid)

    def _prepare_down_payment_product_values(self):
        """Prepare product values for auto-created down payment service."""
        return {
            'name': self.env._('Down payment'),
            'type': 'service',
            'purchase_method': 'purchase',
            'company_id': False,
            'property_account_income_id': self.deposit_account_id.id,
            'supplier_taxes_id': [Command.set(self.deposit_taxes_ids.ids)],
        }

    def action_create_advance_bill(self):
        """Create advance payment bill or deduct from regular bill."""
        purchase_order = self.env['purchase.order'].browse(
            self.env.context.get('active_ids', [])
        )
        if self.advance_payment_method == 'delivered':
            if self.deduct_down_payments:
                purchase_order._deduct_payment(final=self.deduct_down_payments)
            else:
                purchase_order.action_create_invoice()
        else:
            if not self.product_id:
                vals = self._prepare_down_payment_product_values()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_int(
                    'purchase_down_payment.po_deposit_default_product_id',
                    self.product_id.id
                )
            for order in purchase_order:
                amount, _ = self._get_advance_details(order)
                if self.product_id.purchase_method != 'purchase':
                    raise UserError(
                        self.env._(
                            'The product used to invoice a down payment '
                            'should have a control policy set to "On ordered '
                            'quantities". Please update your deposit product.'
                        )
                    )
                if self.product_id.type != 'service':
                    raise UserError(
                        self.env._(
                            "The product used to invoice a down payment "
                            "should be of type 'Service'."
                        )
                    )
                taxes = self.product_id.supplier_taxes_id.filtered(
                    lambda r, ord_co=order.company_id: (
                        not ord_co or r.company_id == ord_co
                    )
                )
                tax_ids = order.fiscal_position_id.map_tax(taxes).ids
                po_line_vals = self._prepare_po_line(order, tax_ids, amount)
                po_line = self.env['purchase.order.line'].create(po_line_vals)
                self._create_bill(order, po_line, amount)

        if self.env.context.get('open_invoices', False):
            return purchase_order.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}
