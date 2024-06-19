# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class AccountPaymentRegister(models.TransientModel):
    """Added custom field bank_charges to add the extra charges"""
    _inherit = 'account.payment.register'

    bank_charges = fields.Monetary(currency_field='currency_id',
                                   related="journal_id.account_id.bank_charge",
                                   string="Bank Charges",
                                   readonly=False,
                                   help="Bank charge amount")

    def _create_payment_vals_from_wizard(self, batch_result):
        """Create payment using values received from wizard."""
        res = super()._create_payment_vals_from_wizard(batch_result)
        res['bank_charges'] = self.bank_charges
        return res

    def _create_payment_vals_from_batch(self, batch_result):
        """Create payment using values received from wizard."""
        res = super(AccountPaymentRegister,
                    self)._create_payment_vals_from_batch(batch_result)
        res['bank_charges'] = self.bank_charges
        return res
