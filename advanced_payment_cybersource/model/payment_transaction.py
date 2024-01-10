"""Payment transaction"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<odoo@cybrosys.com>)
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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PaymentTransaction(models.Model):
    """Inheriting payment.transaction"""
    _inherit = 'payment.transaction'

    capture_manually = fields.Boolean(related='provider_id.capture_manually',
                                      string="Capture Manually",
                                      help='Enable manual capturing')

    def action_cybersource_set_done(self):
        """ Set the state of the demo transaction to 'done'."""
        self.handle_notification()

    def action_cybersource_set_canceled(self):
        """Set the state of the demo transaction to 'cancel'"""
        self.handle_notification()

    def action_cybersource_set_error(self):
        """Set the state of the demo transaction to 'error'"""
        self.handle_notification()

    def handle_notification(self):
        """This is used to handle the notification"""
        self.ensure_one()
        if self.provider_code != 'cybersource':
            return
        notification_data = {'reference': self.reference,
                             'simulated_state': 'error'}
        self._handle_notification_data('cybersource', notification_data)

    @api.model
    def _get_tx_from_notification_data(self, provider_code, data):
        """ Find the transaction based on the notification data."""
        tx = super()._get_tx_from_notification_data(provider_code, data)
        if provider_code != 'cybersource':
            return tx
        reference = data.get('reference')
        tx = self.search(
            [('reference', '=', reference),
             ('provider_code', '=', 'cybersource')])
        if not tx:
            raise ValidationError(
                "Cyber Source " + (
                    "No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """ Update the transaction state and the provider reference based on the
         notification data.
        This method should usually not be called directly. The correct method to
         call upon receiving
        notification data is :meth:`_handle_notification_data`.
        For a provider to handle transaction processing, it must overwrite this
        method and process
        the notification data.
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'cybersource':
            return
        self.provider_reference = f'cybersource-{self.reference}'
        state = notification_data['simulated_state']
        if state == 'pending':
            self._set_pending()
        elif state == 'done':
            if self.capture_manually and not notification_data.get(
                    'manual_capture'):
                self._set_authorized()
            else:
                self._set_done()
                # Immediately post-process the transaction if it is a refund, as
                # the post-processing
                # will not be triggered by a customer browsing the transaction
                # from the portal.
                if self.operation == 'refund':
                    self.env.ref(
                        'payment.cron_post_process_payment_tx')._trigger()
        elif state == 'cancel':
            self._set_canceled()
        else:  # Simulate an error state.
            self._set_error(
                _("You selected the following demo payment status: %s", state))
