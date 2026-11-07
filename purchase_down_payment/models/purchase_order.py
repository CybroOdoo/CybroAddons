# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions
#    (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#
################################################################################
"""Extend purchase order model with down payment deduction logic."""
from odoo import api, models
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools import float_is_zero
from odoo.tools.misc import groupby


class PurchaseOrder(models.Model):
    """Inherit purchase.order to deduct down payments on vendor bills."""

    # pylint: disable=protected-access,too-few-public-methods
    _inherit = 'purchase.order'

    @api.model
    def _nothing_to_invoice_error(self):
        """Show error when there is nothing to bill."""
        return UserError(self.env._(
            "There is nothing to bill!\n\n"
            "Reason(s) of this behavior could be:\n"
            "- You should receive your products before billing them: "
            "Click on the \"truck\" icon "
            "(top-right of your screen) and follow instructions.\n"
            "- You should modify the control policy of your product: "
            "Open the product, go to the "
            "\"Purchase\" tab and modify control policy from "
            "\"On received quantities\" to "
            "\"On ordered quantities\"."
        ))

    def _prepare_deduct_invoice_vals(self, invoice_item_sequence, final=True):
        """Prepare invoice dictionary and lines for a single purchase order."""
        self.ensure_one()
        invoice_vals = self._prepare_invoice()
        invoiceable_lines = self._get_invoiceable_lines(final=final)


        has_product = any(
            not line.display_type or line.display_type == 'product'
            for line in invoiceable_lines
        )
        if not has_product:
            return None, invoice_item_sequence

        invoice_line_vals = []
        down_payment_section_added = False

        for line in invoiceable_lines:
            if not down_payment_section_added and line.is_downpayment:
                invoice_line_vals.append(
                    Command.create(
                        self._prepare_down_payment_section_line(
                            sequence=invoice_item_sequence,
                        )
                    )
                )
                down_payment_section_added = True
                invoice_item_sequence += 1

            optional_values = {'sequence': invoice_item_sequence}
            if line.is_downpayment:
                optional_values['quantity'] = -1.0
            invoice_line_vals.append(
                Command.create(
                    line._prepare_invoice_line(**optional_values)
                )
            )
            invoice_item_sequence += 1

        invoice_vals['invoice_line_ids'] += invoice_line_vals
        return invoice_vals, invoice_item_sequence

    def _group_deduct_invoices(self, invoice_vals_list):
        """Group prepared vendor bill values according to grouping keys."""
        grouping_keys = self._get_invoice_grouping_keys()
        sorted_vals = sorted(
            invoice_vals_list,
            key=lambda x: tuple(x.get(k) for k in grouping_keys)
        )

        grouped_list = []
        for _, invoices in groupby(
            sorted_vals, key=lambda x: tuple(x.get(k) for k in grouping_keys)
        ):
            origins, payment_refs, refs = set(), set(), set()
            ref_vals = None

            for invoice_vals in invoices:
                if not ref_vals:
                    ref_vals = invoice_vals
                else:
                    ref_vals['invoice_line_ids'] += (
                        invoice_vals['invoice_line_ids']
                    )

                origins.add(invoice_vals.get('invoice_origin'))
                payment_refs.add(invoice_vals.get('payment_reference', ''))
                refs.add(invoice_vals.get('ref', ''))

            ref_vals.update({
                'ref': ', '.join(filter(None, refs))[:2000],
                'invoice_origin': ', '.join(filter(None, origins)),
                'payment_reference': (
                    payment_refs.pop() if len(payment_refs) == 1 else False
                ),
            })
            grouped_list.append(ref_vals)

        return grouped_list

    def _fix_invoice_line_sequences(self, invoice_vals_list):
        """Re-sequence invoice lines across grouped invoices."""
        po_line_model = self.env['purchase.order.line']
        for invoice in invoice_vals_list:
            sequence = 1
            for line in invoice['invoice_line_ids']:
                line[2]['sequence'] = (
                    po_line_model._get_invoice_line_sequence(
                        new=sequence,
                        old=line[2]['sequence']
                    )
                )
                sequence += 1

    def _deduct_payment(self, grouped=False, final=False, date=None):
        """Create Vendor Bill associated to Purchase Order."""
        invoice_vals_list = []
        invoice_item_sequence = 0

        for order in self:
            order_ctx = order.with_company(order.company_id)
            inv_vals, invoice_item_sequence = (
                order_ctx._prepare_deduct_invoice_vals(
                    invoice_item_sequence, final=final
                )
            )
            if inv_vals:
                if date:
                    inv_vals['invoice_date'] = date
                invoice_vals_list.append(inv_vals)


        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()

        if not grouped:
            invoice_vals_list = self._group_deduct_invoices(invoice_vals_list)

        if len(invoice_vals_list) < len(self):
            self._fix_invoice_line_sequences(invoice_vals_list)

        moves = self.env['account.move'].sudo().with_context(
            default_move_type='in_invoice'
        ).create(invoice_vals_list)

        moves.sudo().filtered(
            lambda m: m.currency_id.round(m.amount_total) < 0
        ).action_switch_move_type()

        return moves

    @api.model
    def _prepare_down_payment_section_line(self, **optional_values):
        """Prepare Down Payment Section Line."""
        down_payments_section_line = {
            'display_type': 'line_section',
            'name': self.env._('Down Payments'),
            'product_id': False,
            'product_uom_id': False,
            'quantity': 0,
            'discount': 0,
            'price_unit': 0,
            'account_id': False,
        }
        if optional_values:
            down_payments_section_line.update(optional_values)
        return down_payments_section_line

    def _get_invoice_grouping_keys(self):
        """Return invoice grouping keys."""
        return ['company_id', 'partner_id', 'currency_id']

    def _get_invoiceable_lines(self, final=False):
        """Return invoiceable lines including normal and down payment lines."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None

        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure'
        )

        for line in self.order_line:
            if line.display_type == 'line_section':
                pending_section = line
                continue

            if line.is_downpayment:
                down_payment_line_ids.append(line.id)
                continue

            zero_qty = float_is_zero(
                line.qty_to_invoice, precision_digits=precision
            )
            if line.display_type != 'line_note' and zero_qty and not final:
                continue

            if (
                line.qty_to_invoice > 0
                or final
                or line.display_type == 'line_note'
            ):
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)

        return self.env['purchase.order.line'].browse(
            invoiceable_line_ids + down_payment_line_ids
        )
