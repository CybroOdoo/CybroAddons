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
from odoo import api, models


class AccountPayment(models.Model):
    """Inherited the 'account.payment' model to add custom methods."""

    _inherit = "account.payment"

    @api.model
    def create_payment(self, *args):
        """Method to create payment
        Args:
            *args(tuple): A tuple of dictionary that contains journal id ,
            partner id,currency id,amount.
        """
        payment = self.create(
            {
                "journal_id": int(args[0]["journal_id"]),
                "partner_id": int(args[0]["partner_id"]),
                "currency_id": int(args[0]["currency_id"]),
                "amount": int(args[0]["amount"]),
            }
        )
        payment.action_post()
