# -*- coding: utf-8 -*-
##############################################################################
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
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero


class ReturnMove(models.TransientModel):
    """Transient model to enter the reason and generate credit and debit notes."""
    _name = 'return.move'
    _description = 'Return Move'

    reason = fields.Char(string='Reason',
                         help='Specify the reason for credit note',
                         required=True)

    def action_apply_reverse_entry(self):
        """Return the picking and create a reverse entry (credit note / debit note)."""
        active_id = self.env.context.get('active_id')
        if not active_id:
            raise ValidationError(_("No active_id found in the context."))
        return_id = self.env['stock.return.picking'].browse(active_id)
        if not return_id.exists():
            raise ValidationError(_("Return picking wizard record not found."))

        picking_id = return_id.picking_id
        if not picking_id:
            raise ValidationError(_("No original stock picking found."))

        # Verify that posted invoices or bills exist before proceeding
        sale_posted_invoices = self.env['account.move']
        purchase_posted_bills = self.env['account.move']

        if picking_id.sale_id:
            sale_posted_invoices = picking_id.sale_id.invoice_ids.filtered(
                lambda m: m.state == 'posted' and m.move_type == 'out_invoice'
            )
            if not sale_posted_invoices:
                raise ValidationError(
                    _("The selected delivery order must have at least one posted customer invoice to generate a credit note.")
                )
        elif picking_id.purchase_id:
            purchase_posted_bills = picking_id.purchase_id.invoice_ids.filtered(
                lambda m: m.state == 'posted' and m.move_type == 'in_invoice'
            )
            if not purchase_posted_bills:
                raise ValidationError(
                    _("The selected receipt must have at least one posted vendor bill to generate a debit note.")
                )
        else:
            raise ValidationError(
                _("The selected picking is neither linked to a Sales Order nor a Purchase Order.")
            )

        # 1. Create the return picking
        new_picking_res = return_id.action_create_returns()
        new_picking = self.env['stock.picking'].browse(int(new_picking_res['res_id']))

        # Collect returned quantities from the wizard and return picking moves
        returned_quantities = {}
        for return_line in return_id.product_return_moves:
            if return_line.product_id and return_line.quantity > 0:
                returned_quantities[return_line.product_id.id] = (
                    returned_quantities.get(return_line.product_id.id, 0.0) + return_line.quantity
                )

        for move in new_picking.move_ids:
            if float_is_zero(move.quantity, precision_rounding=move.product_uom.rounding) and not float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                move.quantity = move.product_uom_qty
            move.picked = True
            if move.product_id and move.product_id.id not in returned_quantities:
                returned_quantities[move.product_id.id] = (
                    returned_quantities.get(move.product_id.id, 0.0) + (move.quantity or move.product_uom_qty)
                )

        # 2. Validate the return picking in stock
        res_validate = new_picking.with_context(skip_backorder=True, skip_sanity_check=True).button_validate()
        if isinstance(res_validate, dict) and res_validate.get('res_model') == 'stock.backorder.confirmation':
            self.env['stock.backorder.confirmation'].with_context(res_validate.get('context', {})).create({
                'pick_ids': [(6, 0, new_picking.ids)],
            }).process_cancel_backorder()

        # Mark pickings as paid/returned
        picking_id.is_paid = True
        new_picking.is_paid = True

        # 3. Create reverse entry (Credit Note / Debit Note)
        invoices_to_reverse = sale_posted_invoices if picking_id.sale_id else purchase_posted_bills

        # Prioritize posted invoices containing the returned products if multiple exist
        matching_invoices = invoices_to_reverse.filtered(
            lambda inv: any(
                line.product_id.id in returned_quantities
                for line in inv.invoice_line_ids.filtered(lambda l: l.display_type in ('product', False))
            )
        )
        if matching_invoices:
            invoices_to_reverse = matching_invoices

        reversal_wizard = self.env['account.move.reversal'].with_context(
            active_model='account.move',
            active_ids=invoices_to_reverse.ids,
        ).create({
            'move_ids': [fields.Command.set(invoices_to_reverse.ids)],
            'reason': self.reason,
            'date': fields.Date.context_today(self),
            'company_id': invoices_to_reverse[0].company_id.id,
            'journal_id': invoices_to_reverse[0].journal_id.id,
        })
        reversal_wizard.reverse_moves()
        new_moves = reversal_wizard.new_move_ids

        # 4. Adjust credit/debit note line quantities to match the returned quantities
        rem_returned = dict(returned_quantities)
        for move in new_moves:
            product_lines = move.invoice_line_ids.filtered(lambda l: l.display_type in ('product', False))
            has_matching = any(line.product_id.id in rem_returned for line in product_lines)
            if has_matching:
                lines_to_unlink = self.env['account.move.line']
                for line in product_lines:
                    prod_id = line.product_id.id
                    if prod_id in rem_returned and rem_returned[prod_id] > 0.00001:
                        qty = rem_returned[prod_id]
                        if line.quantity > qty:
                            line.quantity = qty
                            rem_returned[prod_id] = 0.0
                        else:
                            rem_returned[prod_id] -= line.quantity
                    else:
                        lines_to_unlink |= line
                if lines_to_unlink and len(move.invoice_line_ids - lines_to_unlink) > 0:
                    lines_to_unlink.unlink()

            # Post the credit / debit note
            if move.state == 'draft':
                move.action_post()

        # 5. Return action to view the created Credit / Debit Note
        if len(new_moves) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Credit Note') if picking_id.sale_id else _('Debit Note'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'target': 'current',
                'res_id': new_moves.id,
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Credit Notes') if picking_id.sale_id else _('Debit Notes'),
                'view_mode': 'list,form',
                'res_model': 'account.move',
                'target': 'current',
                'domain': [('id', 'in', new_moves.ids)],
            }
