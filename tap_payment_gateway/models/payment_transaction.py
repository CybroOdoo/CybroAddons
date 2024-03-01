# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP (odoo@cybrosys.com)
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
from odoo import models, _
from odoo.exceptions import ValidationError


class PaymentTransaction(models.Model):
    """Payment Transaction Model for handling transactions with payment
    providers."""
    _inherit = 'payment.transaction'

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Get the transaction from notification data."""
        tx = super()._get_tx_from_notification_data(provider_code,
                                                    notification_data)
        if provider_code != 'tap' or len(tx) == 1:
            return tx
        reference = notification_data.get(
            'description').split('-')[0]
        tx = self.search(
            [('reference', '=', reference), ('provider_code', '=', 'tap')])
        if not tx:
            raise ValidationError(
                "Tap: " + _("No transaction found matching reference %s.",
                            reference))
        return tx

    def _process_notification_data(self, notification_data):
        """Process the notification data received from Tap"""
        super()._process_notification_data(notification_data)
        if self.provider_code != 'tap':
            return
        self._set_done()
