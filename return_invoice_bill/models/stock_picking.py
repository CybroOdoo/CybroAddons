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


class StockPicking(models.Model):
    """This class extends the 'stock.picking' model to add methods for
    retrieving credit notes and debit notes related to the picking,
    and actions for returning pickings with credit/debit notes."""
    _inherit = 'stock.picking'

    return_invoice_count = fields.Integer(
        string="Return Invoices Count",
        compute='_compute_return_invoice_count',
        help="Count of return credit notes or debit notes",
    )
    is_paid = fields.Boolean(
        copy=False,
        help='Value will be True when return order has created credit/debit note.',
    )

    def _get_related_refund_moves(self):
        """Retrieve credit/debit notes directly linked to this picking or its returns/orders."""
        self.ensure_one()
        AccountMove = self.env['account.move']
        linked_moves = AccountMove.search([
            '|',
            ('origin_picking_id', '=', self.id),
            ('return_picking_id', 'in', (self | self.return_ids).ids)
        ])
        if linked_moves:
            return linked_moves

        if self.sale_id:
            return self.sale_id.invoice_ids.filtered(lambda x: x.move_type == 'out_refund')
        elif self.purchase_id:
            return self.purchase_id.invoice_ids.filtered(lambda x: x.move_type == 'in_refund')
        return AccountMove

    @api.depends('sale_id.invoice_ids', 'purchase_id.invoice_ids', 'is_paid')
    def _compute_return_invoice_count(self):
        for record in self:
            record.return_invoice_count = len(record._get_related_refund_moves())

    def _get_return_wizard_lines_vals(self):
        """Return the one2many commands used to build the wizard return lines."""
        self.ensure_one()
        moves = self.move_ids.filtered(lambda m: m.state == 'done')
        if not moves:
            moves = self.move_ids.filtered(lambda m: m.state not in ('draft', 'cancel'))
        lines_vals = []
        for move in moves:
            uom = move.uom_id or move.product_id.uom_id
            qty = move.quantity if move.quantity > 0 else move.product_uom_qty
            lines_vals.append(fields.Command.create({
                'move_id': move.id,
                'product_id': move.product_id.id,
                'quantity_done': qty,
                'quantity': 0.0,
                'uom_id': uom.id,
            }))
        return lines_vals

    def _get_return_default_journal(self):
        """Return the journal of the posted invoice/bill of the linked order,
        falling back to the first sale/purchase journal of the company."""
        self.ensure_one()
        if self.sale_id:
            invoices = self.sale_id.invoice_ids.filtered(
                lambda i: i.state == 'posted' and i.move_type == 'out_invoice')
        elif self.purchase_id:
            invoices = self.purchase_id.invoice_ids.filtered(
                lambda i: i.state == 'posted' and i.move_type == 'in_invoice')
        else:
            invoices = self.env['account.move']
        if invoices:
            return invoices[0].journal_id
        journal_type = 'sale' if self.picking_type_code == 'outgoing' else 'purchase'
        return self.env['account.journal'].search([
            ('company_id', '=', self.company_id.id),
            ('type', '=', journal_type),
        ], limit=1)

    def _action_open_return_wizard(self):
        self.ensure_one()
        wizard = self.env['return.move'].create({
            'picking_id': self.id,
            'refund_date': fields.Date.context_today(self),
            'journal_id': self._get_return_default_journal().id,
            'auto_post': True,
            'line_ids': self._get_return_wizard_lines_vals(),
        })

        action = self.env["ir.actions.actions"]._for_xml_id("return_invoice_bill.return_move_action")
        action['res_id'] = wizard.id
        action['target'] = 'new'
        action['context'] = dict(self.env.context, active_id=self.id, active_ids=self.ids, active_model='stock.picking')
        return action

    def action_return_with_credit_note(self):
        """Open the return.move wizard to create return picking and credit note."""
        return self._action_open_return_wizard()

    def action_return_with_debit_note(self):
        """Open the return.move wizard to create return picking and debit note."""
        return self._action_open_return_wizard()

    def action_get_credit_note(self):
        """Generates an action to view reversal credit notes."""
        self.ensure_one()
        credit_notes = self._get_related_refund_moves().filtered(lambda x: x.move_type == 'out_refund')
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Credit Notes'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', credit_notes.ids)],
        }

    def action_get_debit_note(self):
        """Generates an action to view reversal debit notes."""
        self.ensure_one()
        debit_notes = self._get_related_refund_moves().filtered(lambda x: x.move_type == 'in_refund')
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Debit Notes'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', debit_notes.ids)],
        }
