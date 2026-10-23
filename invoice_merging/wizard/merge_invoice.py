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
from odoo import fields, models, _
from odoo.exceptions import UserError


class MergeInvoice(models.TransientModel):
    """
    Main method to merge selected invoices
    - If user select merge to existing then the selected invoices will be
      merged to the selected record
    - If no invoice is selected, then a new record will be created with
      lines from the merged invoices
    """
    _name = "merge.invoice"
    _description = "Invoice Merge"

    invoice_ids = fields.Many2many('account.move',
                                   string="Selected Invoices",
                                   help="Selected invoices to merge")
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help="The new invoice will be created"
                                      " for selected partner")

    target_invoice_id = fields.Many2one(
        'account.move',
        string="Merge to existing",
        context={'display_invoice_with_partner': True},
        help="Select an invoice if you want to merge other invoices to selected "
             "one, otherwise leave it empty"
    )

    merge_type = fields.Selection(
        [('cancel', 'Cancel Others'), ('keep', 'Keep Others')],
        string="Merge type", default="cancel",
        help="Select the merge type to decide what to do with other invoices")

    def action_merge_invoice(self):
        """Method for merge invoices"""
        # Checking for is there any exceptions
        if len(self.invoice_ids) <= 1:
            raise UserError(
                _("Merging is not possible on single Invoice or Bill"))
        if any(state in ['posted', 'cancel'] for state in
               self.invoice_ids.mapped('state')):
            raise UserError(_("Merging is only possible on draft state "
                              "Invoices or Bills"))
        if len(set(self.invoice_ids.mapped('move_type'))) > 1:
            raise UserError(_("Merging is only possible for moves of the same type. "
                              "Please select invoices or bills of the same type."))
        if not self.target_invoice_id and not self.partner_id:
            raise UserError(_("Please select a partner for the new merged invoice."))
        # If there is no exceptions continue with the merging
        invoices = self.invoice_ids
        pay_reference = []
        if self.target_invoice_id:
            target_invoice = self.target_invoice_id
            invoices -= self.target_invoice_id
            pay_reference.append(target_invoice.name if target_invoice.name else
                                 f"Draft {str(target_invoice.id)}")
        else:
            source_move = invoices[0]
            target_invoice = self.env['account.move'].with_context(
                check_move_validity=False).create({
                    'partner_id': self.partner_id.id,
                    'move_type': source_move.move_type,
                    'journal_id': source_move.journal_id.id,
                })
        for record in invoices:
            for line in record.line_ids:
                if line.display_type not in ["payment_term", "tax"]:
                    line.with_context(check_move_validity=False).copy(
                        {'move_id': target_invoice.id})
            pay_reference.append(record.name if record.name else
                                 f"Draft {str(record.id)}")
            if self.merge_type == "cancel":
                record.button_cancel()
        target_invoice.write(
            {'payment_reference': f"Merged ({(', '.join(pay_reference))})"})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Merged Invoice'),
            'res_model': 'account.move',
            'res_id': target_invoice.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        }

