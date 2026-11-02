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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class PaymentTransaction(models.Model):
    """
        Issue the movie ticket once the transaction paying a booking invoice
        is confirmed.
    """
    _inherit = 'payment.transaction'

    def _post_process(self):
        """ Override of `payment` to issue the tickets of paid booking invoices.

        Runs after `account_payment` posted the payment, so the invoice
        payment state is up to date. Post-processing is idempotent (core
        flags the transaction) and `_fulfil_booking` guards the invoice too.
        """
        res = super()._post_process()
        for tx in self.filtered(lambda t: t.state == 'done'):
            for invoice in tx.invoice_ids.filtered('movie_booking_data'):
                self.env['movie.registration']._fulfil_booking(invoice)
        return res
