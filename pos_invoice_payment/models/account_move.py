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


class AccountMove(models.Model):
    """Inherited the 'account.move' model to add custom methods."""
    _inherit = "account.move"

    @api.model
    def get_invoices(self):
        """Method to get invoice
        Returns:
            list: A list of dictionaries with invoice details.
        """
        records = self.search([
            ("move_type", "=", "out_invoice"),
            ("payment_state", "!=", "paid"),
        ])
        return [
            {
                "invoice_id": record.id,
                "payment_reference": record.payment_reference,
                "partner_id": record.partner_id.name,
                "amount_total": record.amount_total,
                "amount_residual": record.amount_residual,
                "state": record.state,
                "payment_state": record.payment_state,
            }
            for record in records
        ]

    @api.model
    def register_payment(self, invoice_id):
        """Method to register payment.
        Args:
            invoice_id(int): Id of record to register payment.
        """
        invoice = self.browse(invoice_id)
        if invoice.state != "posted":
            invoice.action_post()

        wiz = self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create({"payment_date": fields.Date.today()})
        return wiz.action_create_payments()

    @api.model
    def post_invoice(self, invoice_id):
        """Method to confirm draft invoices.
        Args:
            invoice_id(int): Id of record to post.
        """
        return self.browse(invoice_id).action_post()
