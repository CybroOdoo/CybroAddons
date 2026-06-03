# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
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
from odoo import fields, models


class AccountPaymentRegister(models.TransientModel):
    """
    Inherit the Account Payment Register model to customize the action of creating payments.

    This class modifies the behavior of the `action_create_payments` method to check if the
    payment relates to a specific type of invoice (e.g., medical, grooming, training, maintenance,
    or medical test invoice). If the invoice's `payment_state` is set to 'paid', the corresponding
    invoice's state is updated, and a closing date is set where applicable.
    """
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        """
        Override the `action_create_payments` method to update the state and closed date
        of various types of invoices when their payment state is marked as 'paid'.

        This method first calls the original `action_create_payments` method, then checks
        for specific types of invoices related to the payment. Depending on the type, if
        the `payment_state` is 'paid', it performs the following actions:

        - Sets the `state` to 'close' or 'complete', depending on the invoice type.
        - Sets the `closed_date` to the current date for applicable invoice types.

        Returns:
            action: The result of the original `action_create_payments` method.
        """
        action = super().action_create_payments()

        # Update state and closed_date for medical bill invoices
        if self.line_ids.move_id.medical_bill_invoice_id:
            if self.line_ids.move_id.payment_state == 'paid':
                self.line_ids.move_id.medical_bill_invoice_id.write(
                    {'state': 'close'})
                self.line_ids.move_id.medical_bill_invoice_id.closed_date = fields.Date.today()
        # Update state and closed_date for grooming bill invoices
        elif self.line_ids.move_id.grooming_bill_invoice_id:
            if self.line_ids.move_id.payment_state == 'paid':
                self.line_ids.move_id.grooming_bill_invoice_id.write(
                    {'state': 'close'})
                self.line_ids.move_id.grooming_bill_invoice_id.closed_date = fields.Date.today()
        # Update state and closed_date for training bill invoices
        elif self.line_ids.move_id.training_bill_invoice_id:
            if self.line_ids.move_id.payment_state == 'paid':
                self.line_ids.move_id.training_bill_invoice_id.write(
                    {'state': 'close'})
                self.line_ids.move_id.training_bill_invoice_id.closed_date = fields.Date.today()
        # Update state for maintenance bill invoices
        elif self.line_ids.move_id.maintenance_bill_invoice_id:
            if self.line_ids.move_id.payment_state == 'paid':
                self.line_ids.move_id.maintenance_bill_invoice_id.write(
                    {'state': 'complete'})
        # Update state for medical test bill invoices
        elif self.line_ids.move_id.medical_test_bill_invoice_id:
            if self.line_ids.move_id.payment_state == 'paid':
                self.line_ids.move_id.medical_test_bill_invoice_id.write(
                    {'state': 'complete'})
        return action
