# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
##############################################################################
from odoo import api, models


class PosOrder(models.Model):
    """This class extends the 'pos.order' model and adds custom functionality
    related to payment processing."""
    _inherit = 'pos.order'

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        """Prepare and return a dictionary containing payment fields from the
         user interface payment line.
        params:
        order (pos.order): The POS order to which the payment belongs.
        ui_paymentline (dict): Payment information from the user interface."""
        return {
            'amount': ui_paymentline['amount'] or 0.0,
            'payment_date': ui_paymentline['name'],
            'payment_method_id': ui_paymentline['payment_method_id'],
            'card_type': ui_paymentline.get('card_type'),
            'cardholder_name': ui_paymentline.get('cardholder_name'),
            'transaction_id': ui_paymentline.get('transaction_id'),
            'payment_status': ui_paymentline.get('payment_status'),
            'ticket': ui_paymentline.get('ticket'),
            'pos_order_id': order.id,
            'payment_currency': ui_paymentline.get('payment_currency'),
            'currency_amount': ui_paymentline.get('currency_amount')
        }
