# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
################################################################################
"""Module to handle Account Move related logic."""

from odoo import api, fields, models


class AccountMove(models.Model):
    """Inherited the 'account.move' model to add custom methods."""

    _inherit = "account.move"

    @api.model
    def get_invoices(self):
        """Method to get invoice
        Returns:
         dict:A dictionary of invoice id,payment reference,partner name,
         total amount,amount residual,state and payment state
        """
        invoice_list = [
            {
                "invoice_id": record.id,
                "payment_reference": record.payment_reference,
                "partner_id": record.partner_id.name,
                "amount_total": record.amount_total,
                "amount_residual": record.amount_residual,
                "state": record.state,
                "payment_state": record.payment_state,
            }
            for record in self.search([("move_type", "=", "out_invoice")])
        ]
        return invoice_list

    @api.model
    def register_payment(self, invoice):
        """Method to register payment,
        Args:
            *args(int):Id of record to register payment.
        """
        self.browse(invoice).action_register_payment()
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice
        ).create({"payment_date": fields.date.today()}).action_create_payments()

    @api.model
    def post_invoice(self, invoice_id):
        """Method to confirm non posted invoices,
        Args:
            *args(int):Id of record to post journal.
        """
        self.browse(invoice_id).action_post()
