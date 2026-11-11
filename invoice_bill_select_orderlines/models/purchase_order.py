###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, groupby


class PurchaseOrderLine(models.Model):
    """Inherits the purchase order line"""
    _inherit = 'purchase.order.line'

    is_product_select = fields.Boolean(
        string="Select",
        help="To select Products from Order lines",
        copy=False)


class PurchaseOrder(models.Model):
    """Inherits the purchase order"""
    _inherit = 'purchase.order'

    all_lines_selected = fields.Boolean(
        compute="_compute_selection_states",
        help="Indicates whether all invoiceable order lines are selected.")
    any_line_selected = fields.Boolean(
        compute="_compute_selection_states",
        help="Indicates whether at least one invoiceable order line is "
             "selected.")

    def action_select_all(self):
        """Select all the products from the purchase order line for bill"""
        self.order_line.filtered(lambda rec: rec.qty_to_invoice > 0).write(
            {'is_product_select': True})

    def action_deselect_all(self):
        """Deselect all the products from the purchase order line for bill"""
        self.order_line.filtered(lambda rec: rec.qty_to_invoice > 0).write(
            {'is_product_select': False})

    @api.depends('order_line.is_product_select', 'order_line.qty_to_invoice')
    def _compute_selection_states(self):
        """Compute the selection status of invoiceable purchase order lines.

           Sets ``all_lines_selected`` to True when all invoiceable lines are
           selected, and ``any_line_selected`` to True when at least one
           invoiceable line is selected.
           """
        for order in self:
            selectable_lines = order.order_line.filtered(
                lambda line: line.qty_to_invoice > 0)
            selected = selectable_lines.mapped('is_product_select')
            order.all_lines_selected = bool(selected) and all(selected)
            order.any_line_selected = any(selected)

    def _check_selected_lines(self):
        """Raise an error when no invoiceable order line is selected.

        Only lines that still have something to invoice count as selected,
        so an already billed line with an old selection is ignored."""
        if not self.order_line.filtered(
                lambda line: line.is_product_select
                and line.qty_to_invoice > 0):
            raise UserError(self.env._(
                "There is no invoiceable line. Please make sure that an "
                "order line is selected"))

    def action_create_invoice(self, *args, **kwargs):
        """Create vendor bill based on selected order lines."""
        # Odoo 19 "Upload Bill" calls this method with extra arguments
        # (e.g. the uploaded attachments). Standard Odoo creates that bill,
        # then we keep only the selected lines on it.
        if args or kwargs:
            return self._action_upload_bill_selected(*args, **kwargs)
        self._check_selected_lines()
        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        sequence = 10
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit')
        for order in self:
            if order.invoice_status != 'to invoice':
                continue
            order = order.with_company(order.company_id)
            pending_section = None
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            lines = order.order_line.filtered(
                lambda line: line.is_product_select
                or line.display_type == 'line_section')
            for line in lines:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice,
                                 precision_digits=precision):
                    continue
                if pending_section:
                    line_vals = pending_section._prepare_account_move_line()
                    line_vals.update({'sequence': sequence})
                    invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                    sequence += 1
                    pending_section = None
                line_vals = line._prepare_account_move_line()
                line_vals.update({'sequence': sequence})
                invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                sequence += 1
            if invoice_vals['invoice_line_ids']:
                invoice_vals_list.append(invoice_vals)
        if not invoice_vals_list:
            raise UserError(self.env._(
                "There is no invoiceable line. If a product has a control "
                "policy based on received quantity, please make sure that "
                "a quantity has been received."))
        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for _keys, invoices in groupby(
                invoice_vals_list,
                key=lambda x: (x.get('company_id'), x.get('partner_id'),
                               x.get('currency_id'))):
            new_invoice_vals_list.append(
                self.get_ref_invoice_vals(invoices=invoices))
        invoice_vals_list = new_invoice_vals_list
        # 3) Create invoices.
        moves = self.env['account.move']
        for vals in invoice_vals_list:
            moves |= self.env['account.move'].with_context(
                default_move_type='in_invoice').with_company(
                vals['company_id']).create(vals)
        # 4) Some moves might actually be refunds: convert them if the total
        # amount is negative. We do this after the moves have been created
        # since we need taxes, etc. to know if the total is negative or not.
        moves.filtered(
            lambda m: m.currency_id.round(m.amount_total) < 0,
        ).action_switch_move_type()
        # Clear the selection once the bill is created
        self.order_line.filtered('is_product_select').write(
            {'is_product_select': False})
        return self.action_view_invoice(moves)

    def _action_upload_bill_selected(self, *args, **kwargs):
        """Run the standard Upload Bill flow, then remove the lines that
        were not selected from the bill(s) it created."""
        self._check_selected_lines()
        unselected = self.order_line.filtered(
            lambda line: not line.display_type and not line.is_product_select)
        invoices_before = self.invoice_ids
        # The standard method is deliberately called from this helper.
        # pylint: disable=super-method-mismatch
        result = super().action_create_invoice(*args, **kwargs)
        self.invalidate_recordset(['invoice_ids'])
        new_moves = self.invoice_ids - invoices_before
        for move in new_moves.filtered(lambda m: m.state == 'draft'):
            commands = []
            product_lines = move.invoice_line_ids.filtered(
                lambda line: line.display_type not in (
                    'line_section', 'line_note'))
            removed = product_lines.filtered(
                lambda line: line.purchase_line_id in unselected)
            commands += [(2, line.id) for line in removed]
            # Drop sections that no longer have any product line under them.
            kept = product_lines - removed
            section = None
            section_has_lines = False
            for line in move.invoice_line_ids.sorted(
                    lambda rec: (rec.sequence, rec.id)):
                if line.display_type == 'line_section':
                    if section and not section_has_lines:
                        commands.append((2, section.id))
                    section, section_has_lines = line, False
                elif line in kept:
                    section_has_lines = True
            if section and not section_has_lines:
                commands.append((2, section.id))
            if commands:
                move.write({'invoice_line_ids': commands})
        # Clear the selection once the bill is created
        self.order_line.filtered('is_product_select').write(
            {'is_product_select': False})
        return result

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
            origins.add(invoice_vals.get('invoice_origin', ''))
            payment_refs.add(invoice_vals.get('payment_reference', False))
            refs.add(invoice_vals.get('ref', ''))
        ref_invoice_vals.update({
            'ref': ', '.join(refs)[:2000],
            'invoice_origin': ', '.join(origins),
            'payment_reference': ((len(payment_refs) == 1
                                  and payment_refs.pop()) or False),
        })
        return ref_invoice_vals
