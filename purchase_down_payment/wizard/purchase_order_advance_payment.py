# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ashwin T (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
##############################################################################
import time
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.fields import Command


class PurchaseOrderAdvancePayment(models.TransientModel):
    """The class is created to creating a new model purchase order advance
    payment."""
    _name = 'purchase.order.advance.payment'
    _description = 'Purchase Order Advance Payment Bill'

    @api.model
    def _default_product_id(self):
        """Function to fetch the purchase down payment default product"""
        product_id = self.env['ir.config_parameter'].sudo().get_param(
            'purchase_down_payment.po_deposit_default_product_id')
        return self.env['product.product'].browse(int(product_id)).exists()

    @api.model
    def _default_currency_id(self):
        """Function to fetch the currency_id from purchase order"""
        if self._context.get(
                'active_model') == 'purchase.order' and self._context.get(
            'active_id', False):
            purchase_order = self.env['purchase.order'].browse(
                self._context.get('active_id'))
            return purchase_order.currency_id

    @api.model
    def _default_has_down_payment(self):
        """Function to check the Purchase order has down payment or not"""
        if self._context.get(
                'active_model') == 'purchase.order' and self._context.get(
            'active_id', False):
            purchase_order = self.env['purchase.order'].browse(
                self._context.get('active_id'))
            return purchase_order.order_line.filtered(
                lambda purchase_order_line: purchase_order_line.is_downpayment
            )
        return False

    advance_payment_method = fields.Selection([
        ('delivered', 'Regular bill'),
        ('percentage', 'Down payment (percentage)'),
        ('fixed', 'Down payment (fixed amount)')
    ], string='Create Bill', default='delivered', required=True,
        help="A standard bill is issued with all the order lines ready "
             "for billing, \
        according to their billing policy (based on ordered or delivered "
             "quantity).")
    has_down_payments = fields.Boolean(string='Has down payments',
                                       default=_default_has_down_payment,
                                       readonly=True,
                                       help='To check the invoice in down '
                                            'payment or not')
    product_id = fields.Many2one('product.product',
                                 string='Down Payment Product',
                                 domain=[('type', '=', 'service')],
                                 default=_default_product_id,
                                 help='To add the down payment product')
    deduct_down_payments = fields.Boolean(string='Deduct down payments',
                                          default=False,
                                          help='To mention the down payment '
                                               'amount deduct to next invoice')
    amount = fields.Float(string='Down Payment Amount', digits='Account',
                          help="The percentage of amount to be bill in "
                               "advance, taxes excluded.")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=_default_currency_id,
                                  help='Default company currency')
    fixed_amount = fields.Monetary(string='Down Payment Amount (Fixed)',
                                   help="The fixed amount to be bill in "
                                        "advance, taxes excluded.")
    deposit_account_id = fields.Many2one('account.account',
                                         string="Income Account",
                                         domain=[('deprecated', '=', False)],
                                         help="Account used for deposits")
    deposit_taxes_ids = fields.Many2many('account.tax',
                                         string="Customer Taxes",
                                         domain=[
                                             ('type_tax_use', '=', 'purchase')],
                                         help="Taxes used for deposits")

    def _get_advance_details(self, order):
        """Function to find get the down payment amount and purchase order"""
        if self.advance_payment_method == 'percentage':
            if all(self.product_id.taxes_id.mapped('price_include')):
                amount = order.amount_total * self.amount / 100
            else:
                amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount)
        else:
            amount = self.fixed_amount
            name = _('Down Payment')
        context = {'lang': order.partner_id.lang}
        del context
        return amount, name

    def _prepare_po_line(self, order, tax_ids, amount):
        """Function to getting the purchase order line data"""
        context = {'lang': order.partner_id.lang}
        po_values = {
            'name': _('Down Payment: %s / %s') % (
                time.strftime('%m-%Y-%d'), order.name),
            'price_unit': amount,
            'product_uom_qty': 0.0,
            'product_qty': 0.0,
            'order_id': order.id,
            'product_uom': self.product_id.uom_id.id,
            'product_id': self.product_id.id,
            'taxes_id': [(6, 0, tax_ids)],
            'is_downpayment': True,
            'sequence': order.order_line and order.order_line[
                -1].sequence + 1 or 10,
            'date_planned': datetime.today(),
        }
        del context
        return po_values

    def _prepare_invoice_values(self, order, name, amount, so_line):
        """Function for take invoice values"""
        invoice_vals = {
            'ref': order.partner_ref or '',
            'move_type': 'in_invoice',
            'invoice_origin': order.name,
            'invoice_user_id': order.user_id.id,
            'narration': order.notes,
            'partner_id': order.partner_id.id,
            'fiscal_position_id': (
                    order.fiscal_position_id or
                    order.fiscal_position_id._get_fiscal_position(
                order.partner_id)).id,
            'currency_id': order.currency_id.id,
            'payment_reference': order.partner_ref or '',
            'invoice_payment_term_id': order.payment_term_id.id,
            'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'price_unit': amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'purchase_line_id': so_line.id,
                'product_uom_id': so_line.product_uom.id,
            })],
        }
        return invoice_vals

    def _create_bill(self, order, so_line, amount):
        """Function for creating the purchase bill"""
        if (
                self.advance_payment_method == 'percentage' and self.amount <=
                0.00) or (
                self.advance_payment_method == 'fixed' and self.fixed_amount <=
                0.00):
            raise UserError(
                _('The value of the down payment amount must be positive.'))
        amount, name = self._get_advance_details(order)
        invoice_vals = self._prepare_invoice_values(order, name, amount,
                                                    so_line)
        if order.fiscal_position_id:
            invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id
        invoice = self.env['account.move'].with_company(order.company_id) \
            .sudo().create(invoice_vals).with_user(self.env.uid)
        return invoice

    def _prepare_down_payment_product_values(self):
        return {
            'name': _('Down payment'),
            'type': 'service',
            'invoice_policy': 'order',
            'company_id': False,
            'property_account_income_id': self.deposit_account_id.id,
            'taxes_id': [Command.set(self.deposit_taxes_ids.ids)],
        }

    def action_create_advance_bill(self):
        """Function for creating purchase down payment bill"""
        purchase_order = self.env['purchase.order'].browse(
            self._context.get('active_ids', []))
        if self.advance_payment_method == 'delivered':
            if self.deduct_down_payments:
                purchase_order._deduct_payment(final=self.deduct_down_payments)
            else:
                purchase_order.action_create_invoice()
        else:
            if not self.product_id:
                vals = self._prepare_down_payment_product_values()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param(
                    'purchase_down_payment.po_deposit_default_product_id',
                    self.product_id.id)
            purchase_line_obj = self.env['purchase.order.line']
            for order in purchase_order:
                amount, name = self._get_advance_details(order)
                if self.product_id.invoice_policy != 'order':
                    raise UserError(
                        _('The product used to invoice a down payment should '
                          'have an invoice policy set to "Ordered '
                          'quantities". Please update your deposit product to '
                          'be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(
                        _("The product used to invoice a down payment should "
                          "be of type 'Service'. Please use another product "
                          "or update this product."))
                taxes = self.product_id.taxes_id.filtered(
                    lambda
                        r: not order.company_id or r.company_id == order.company_id)
                tax_ids = order.fiscal_position_id.map_tax(taxes).ids
                po_line_values = self._prepare_po_line(order,
                                                       tax_ids, amount)
                po_line = purchase_line_obj.create(po_line_values)
                self._create_bill(order, po_line, amount)
                if self._context.get('open_invoices', False):
                    return purchase_order.action_view_invoice()
            return {'type': 'ir.actions.act_window_close'}
        if self._context.get('open_invoices', False):
            return purchase_order.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}
