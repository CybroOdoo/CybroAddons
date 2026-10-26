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
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ReturnMove(models.TransientModel):
    """Transient model to process return pickings with automated Credit/Debit Note generation."""
    _name = 'return.move'
    _description = 'Return Move'

    picking_id = fields.Many2one(
        'stock.picking',
        string='Original Picking',
        required=True,
    )
    picking_type_code = fields.Selection(
        related='picking_id.picking_type_code',
        string='Picking Type',
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='picking_id.partner_id',
        string='Partner',
    )
    company_id = fields.Many2one(
        'res.company',
        related='picking_id.company_id',
        string='Company',
    )
    reason = fields.Char(
        string='Reason / Reference',
        help='Specify the reason or reference for the Credit/Debit note',
    )
    refund_date = fields.Date(
        default=fields.Date.context_today,
        required=True,
    )
    journal_id = fields.Many2one(
        'account.journal',
        domain="[('company_id', '=', company_id), ('type', '=', 'sale' if picking_type_code == 'outgoing' else 'purchase')]",
        help='Accounting journal for the Credit Note or Debit Note.',
    )
    auto_post = fields.Boolean(
        string='Auto-post Note',
        default=True,
        help='Automatically post the generated Credit Note or Debit Note.',
    )
    line_ids = fields.One2many(
        'return.move.line',
        'wizard_id',
        string='Return Lines',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('picking_id') and not vals.get('line_ids'):
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                if picking.exists():
                    vals['line_ids'] = picking._get_return_wizard_lines_vals()
        return super().create(vals_list)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        raw_picking_id = (
            self.env.context.get('default_picking_id')
            or self.env.context.get('active_id')
            or res.get('picking_id')
        )
        picking_id = False
        if isinstance(raw_picking_id, int):
            picking_id = raw_picking_id
        elif isinstance(raw_picking_id, (list, tuple)) and raw_picking_id:
            first = raw_picking_id[0]
            if isinstance(first, int):
                picking_id = first
            elif isinstance(first, (list, tuple)) and len(first) >= 3 and first[2]:
                picking_id = first[2][0]

        picking = self.env['stock.picking'].browse(picking_id).exists()
        if picking:
            res['picking_id'] = picking.id
            res['journal_id'] = picking._get_return_default_journal().id
            res['line_ids'] = picking._get_return_wizard_lines_vals()
        return res

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id:
            self.line_ids = self.picking_id._get_return_wizard_lines_vals()

    def action_apply_reverse_entry(self):
        """Return the picking lines and generate & link credit/debit note."""
        self.ensure_one()
        if not self.reason or not self.reason.strip():
            raise ValidationError(self.env._("Please specify a Reason / Reference for the Credit/Debit note."))

        picking = self.picking_id
        if not picking or picking.state != 'done':
            raise ValidationError(self.env._("Returns can only be processed for Pickings in 'Done' state."))

        if not self.line_ids:
            raise ValidationError(self.env._("No items found to return."))

        for line in self.line_ids:
            if line.quantity <= 0:
                raise ValidationError(
                    self.env._("The return quantity for '%(product)s' must be greater than zero.",
                      product=line.product_id.display_name)
                )
            if line.quantity > line.quantity_done:
                raise ValidationError(
                    self.env._("Cannot return more than the delivered/received quantity (%(max_qty)s %(uom)s) for %(product)s.",
                      max_qty=line.quantity_done,
                      uom=line.uom_id.name,
                      product=line.product_id.display_name)
                )

        sale_invoices = picking.sale_id.invoice_ids.filtered(lambda i: i.move_type == 'out_invoice' and i.state == 'posted')
        purchase_bills = picking.purchase_id.invoice_ids.filtered(lambda i: i.move_type == 'in_invoice' and i.state == 'posted')

        if picking.sale_id and not sale_invoices:
            raise ValidationError(self.env._("The linked Sales Order must have at least one posted customer invoice."))
        if picking.purchase_id and not purchase_bills:
            raise ValidationError(self.env._("The linked Purchase Order must have at least one posted vendor bill."))

        # 1. Create return picking
        new_picking = picking._create_return()

        # 2. Adjust quantities on return picking moves and unlink unselected moves
        line_by_move = {l.move_id.id: l.quantity for l in self.line_ids}
        moves_to_unlink = self.env['stock.move']

        for move in new_picking.move_ids:
            orig_move_id = move.origin_returned_move_id.id
            qty_to_return = line_by_move.get(orig_move_id, 0.0)
            if qty_to_return > 0:
                move.product_uom_qty = qty_to_return
                move.quantity = qty_to_return
            else:
                moves_to_unlink |= move

        if moves_to_unlink:
            moves_to_unlink.unlink()

        # 3. Confirm and validate return picking
        new_picking.action_confirm()
        new_picking.action_assign()
        for move in new_picking.move_ids:
            move.quantity = move.product_uom_qty

        new_picking.with_context(
            skip_backorder=True, skip_sms=True, skip_immediate=True,
        ).button_validate()
        if new_picking.state != 'done':
            raise UserError(self.env._(
                "The return picking %(picking)s could not be validated automatically. "
                "Please check the stock availability and try again.",
                picking=new_picking.display_name,
            ))

        picking.is_paid = True
        new_picking.is_paid = True

        # 4. Generate Credit Note or Debit Note
        move_id = self._create_credit_or_debit_note(picking, new_picking, self.line_ids)

        if move_id:
            doc_link = move_id._get_html_link()
            picking.message_post(body=self.env._(
                "Return picking %(return_picking)s created with refund note %(refund_note)s. Reason: %(reason)s",
                return_picking=new_picking._get_html_link(),
                refund_note=doc_link,
                reason=self.reason,
            ))
            new_picking.message_post(body=self.env._(
                "Created from picking %(origin_picking)s with refund note %(refund_note)s. Reason: %(reason)s",
                origin_picking=picking._get_html_link(),
                refund_note=doc_link,
                reason=self.reason,
            ))
            move_id.message_post(body=self.env._(
                "Generated from return picking %(return_picking)s for reason: %(reason)s",
                return_picking=new_picking._get_html_link(),
                reason=self.reason,
            ))

            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.move',
                'target': 'current',
                'res_id': move_id.id,
            }

        return {'type': 'ir.actions.act_window_close'}

    def _create_credit_or_debit_note(self, picking, new_picking, return_lines):
        """Create and configure the Credit Note or Debit Note."""
        move_id = self.env['account.move']
        if picking.sale_id:
            order = picking.sale_id
            invoice_type, refund_type = 'out_invoice', 'out_refund'
        elif picking.purchase_id:
            order = picking.purchase_id
            invoice_type, refund_type = 'in_invoice', 'in_refund'
        else:
            return move_id

        # Let the order create the refund itself when its invoicing policy
        # allows it. It raises a UserError when there is nothing to invoice,
        # in which case the posted invoice is reversed instead.
        existing_ids = set(order.invoice_ids.ids)
        try:
            with self.env.cr.savepoint():
                if picking.sale_id:
                    order._create_invoices(final=True)
                else:
                    order.action_create_invoice()
        except UserError:
            pass
        new_refunds = order.invoice_ids.filtered(
            lambda i: i.id not in existing_ids and i.move_type == refund_type)
        if new_refunds:
            move_id = new_refunds[0]
        else:
            posted_invoices = order.invoice_ids.filtered(
                lambda i: i.move_type == invoice_type and i.state == 'posted')
            if posted_invoices:
                primary_invoice = posted_invoices[0]
                reverse_moves = primary_invoice._reverse_moves([{
                    'ref': self.reason,
                    'date': self.refund_date,
                    'invoice_date': self.refund_date,
                    'journal_id': self.journal_id.id or primary_invoice.journal_id.id,
                    'origin_picking_id': picking.id,
                    'return_picking_id': new_picking.id,
                }])
                if reverse_moves:
                    move_id = reverse_moves[0]
                    self._adjust_refund_invoice_lines(move_id, return_lines)

        if move_id:
            move_id.ref = self.reason
            move_id.invoice_date = self.refund_date
            move_id.origin_picking_id = picking.id
            move_id.return_picking_id = new_picking.id
            if self.journal_id:
                move_id.journal_id = self.journal_id
            if self.auto_post and move_id.state == 'draft':
                move_id.action_post()

        return move_id

    def _adjust_refund_invoice_lines(self, move_id, return_lines):
        """Adjust line quantities on the reversed credit note to match actual returned quantities."""
        returned_product_qty = {}
        for r_line in return_lines:
            returned_product_qty[r_line.product_id.id] = (
                returned_product_qty.get(r_line.product_id.id, 0.0) + r_line.quantity
            )

        for inv_line in move_id.invoice_line_ids:
            if inv_line.display_type in ('line_section', 'line_note'):
                continue
            prod_id = inv_line.product_id.id
            if prod_id in returned_product_qty and returned_product_qty[prod_id] > 0:
                inv_line.quantity = returned_product_qty[prod_id]
                returned_product_qty[prod_id] = 0
            else:
                inv_line.unlink()


class ReturnMoveLine(models.TransientModel):
    """Transient model to manage items and quantities returned."""
    _name = 'return.move.line'
    _description = 'Return Move Line'

    wizard_id = fields.Many2one('return.move', ondelete='cascade')
    move_id = fields.Many2one('stock.move', string='Stock Move', required=True)
    product_id = fields.Many2one('product.product', required=True)
    quantity_done = fields.Float(string='Delivered / Received', readonly=True)
    quantity = fields.Float(string='Return Quantity', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)
