# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Raneesha MK (odoo@cybrosys.com)
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
from odoo import models


class AccountMove(models.Model):
    """inherit the class account_move"""
    _inherit = "account.move"

    def action_post(self):
        """super the action_post() to change service_booking state into
        invoice"""
        res = super(AccountMove, self).action_post()
        if self:
            if self.invoice_origin in self.env["service.booking"].search(
                    []).mapped("reference_no"):
                booking_id = self.env["service.booking"].search(
                    [("reference_no", "=", self.invoice_origin)])
                amount = sum(self.search(
                    [("invoice_origin", "=", booking_id.reference_no),
                     ("state", "!=", "cancel")]
                ).mapped("amount_untaxed_signed"))
                if booking_id.service_package_price == amount:
                    booking_id.write({"state": "invoice"})
        return res

    def button_cancel(self):
        """Inherit the 'button_cancel' method to update related service
        bookings' states when an invoice is canceled."""
        result = super(AccountMove, self).button_cancel()
        if self.invoice_origin in self.env["service.booking"].search([]).mapped(
                "reference_no"):
            booking_id = self.env["service.booking"].search(
                [("reference_no", "=", self.invoice_origin)])
            booking_id.write({"state": "confirm"})
        return result

    def button_draft(self):
        """Inherit the 'button_draft' method to set related 'service.booking'
        records to 'to_invoice' state.This method first calls the super method
        to revert the invoice to 'draft' state.It then checks if the invoice is
        linked to any 'service.booking' records.
        If so, it sets the 'state' of those records to 'to_invoice' to indicate
        that they need to be invoiced.
        :return: Result of the 'button_draft' method"""
        result = super(AccountMove, self).button_draft()
        if self.invoice_origin in self.env["service.booking"].search([]).mapped(
                "reference_no"):
            booking_id = self.env["service.booking"].search(
                [("reference_no", "=", self.invoice_origin)])
            booking_id.write({"state": "to_invoice"})
        return result
