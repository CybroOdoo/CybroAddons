# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Hafeesul Ali(<https://www.cybrosys.com>)
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
#############################################################################
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
    def register_payment(self, *args):
        """Method to register payment,
        Args:
            *args(int):Id of record to register payment.
        """
        payment = self.browse(*args).action_register_payment()
        invoice_id = payment["context"]["active_ids"][0]
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice_id
        ).create({"payment_date": fields.date.today()}).action_create_payments()

    @api.model
    def post_invoice(self, *args):
        """Method to confirm non posted invoices,
        Args:
            *args(int):Id of record to post journal.
        """
        self.browse(*args).action_post()
