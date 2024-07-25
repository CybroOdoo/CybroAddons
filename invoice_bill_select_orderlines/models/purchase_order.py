# -*- coding: utf-8 -*-
"""
Can use only selected products to invoice as well as bills.
"""
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, groupby


class PurchaseOrderLine(models.Model):
    """Inherits the purchase order line"""
    _inherit = 'purchase.order.line'

    is_product_select = fields.Boolean(string="Select", help="To select Products from Order lines", copy=False)


class PurchaseOrder(models.Model):
    """Inherits the purchase order"""
    _inherit = 'purchase.order'

    def action_select_all(self):
        """Select all the products from the sale order line for invoice"""
        self.order_line.filtered(lambda rec: rec.qty_to_invoice > 0).write(
            {'is_product_select': True})

    def action_deselect_all(self):
        """Deselect all the products from the sale order line for invoice"""
        self.order_line.filtered(lambda rec: rec.qty_to_invoice > 0).write(
            {'is_product_select': False})

    def action_create_invoice(self):
        """Create the invoice associated to the PO and Update the invoiceable
         lines on the basis of selected lines"""
        if self.order_line.filtered(
                lambda selected: selected.is_product_select):
            # 1) Prepare invoice vals and clean-up the section lines
            invoice_vals_list = []
            sequence = 10
            for order in self:
                if order.invoice_status != 'to invoice':
                    continue
                order = order.with_company(order.company_id)
                pending_section = None
                # Invoice values.
                invoice_vals = order._prepare_invoice()
                # Invoice line values (keep only necessary sections).
                for line in order.order_line.filtered(lambda line_select: (
                                                                                  line_select.is_product_select) or True not in
                                                                          self.order_line.mapped(
                                                                              'is_product_select') or
                                                                          line_select.display_type == 'line_section'):
                    if line.display_type == 'line_section':
                        pending_section = line
                        continue
                    if not float_is_zero(line.qty_to_invoice,
                                         precision_digits=self.env[
                                             'decimal.precision'].precision_get(
                                             'Product Unit of Measure')):
                        if pending_section:
                            line_vals = pending_section._prepare_account_move_line()
                            line_vals.update({'sequence': sequence})
                            invoice_vals['invoice_line_ids'].append(
                                (0, 0, line_vals))
                            sequence += 1
                            pending_section = None
                        line_vals = line._prepare_account_move_line()
                        line_vals.update({'sequence': sequence})
                        invoice_vals['invoice_line_ids'].append(
                            (0, 0, line_vals))
                        sequence += 1
                invoice_vals_list.append(invoice_vals)
            if not invoice_vals_list:
                raise UserError(
                    _('There is no invoiceable line. If a product has a'
                      ' control policy based on received quantity, '
                      'please make sure that a quantity has been '
                      'received.'))
            # 2) group by (company_id, partner_id, currency_id) for batch creation
            new_invoice_vals_list = []
            for grouping_keys, invoices in groupby(
                    invoice_vals_list,
                    key=lambda x: (x.get('company_id'), x.get(
                        'partner_id'), x.get('currency_id'))):
                ref_invoice_vals = self.get_ref_invoice_vals(invoices=invoices)
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list
            # 3) Create invoices.
            moves = self.env['account.move']
            if invoice_vals_list[0].get('invoice_line_ids'):
                for vals in invoice_vals_list:
                    moves |= self.env['account.move'].with_context(
                        default_move_type='in_invoice').with_company(
                        vals['company_id']).create(
                        vals)
                # 4) Some moves might actually be refunds: convert them if the
                # total amount is negative
                # We do this after the moves have been created since we need taxes,
                # 'etc. to know if the total
                # is actually negative or not
                moves.filtered(
                    lambda m: m.currency_id.round(m.amount_total) < 0) \
                    .action_switch_move_type()
                return self.action_view_invoice(moves)
            raise UserError(
                _('There is no invoiceable line. Please make sure '
                  'that a order line is selected'))
        raise UserError(_('There is no invoiceable line. Please make sure '
                          'that a order line is selected'))

    def get_ref_invoice_vals(self, invoices):
        """
        This is the method get_ref_invoice_vals which will return the invoice
        vals to the method
        """
        origins = set()
        payment_refs = set()
        refs = set()
        ref_invoice_vals = {}
        for invoice_vals in invoices:
            if not ref_invoice_vals:
                ref_invoice_vals = invoice_vals
            else:
                ref_invoice_vals['invoice_line_ids'] += invoice_vals[
                    'invoice_line_ids']
            origins.add(invoice_vals['invoice_origin'])
            payment_refs.add(invoice_vals['payment_reference'])
            refs.add(invoice_vals['ref'])
        ref_invoice_vals.update({
            'ref': ', '.join(refs)[:2000],
            'invoice_origin': ', '.join(origins),
            'payment_reference': len(
                payment_refs) == 1 and payment_refs.pop() or False,
        })
        return ref_invoice_vals
