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
#############################################################################
from odoo import api, models


class MailingSubscription(models.Model):
    """Send the mail on subscription of the mailing lists."""
    _inherit = 'mailing.subscription'

    @api.model_create_multi
    def create(self, vals_list):
        """Send the subscription template of the list to the contacts who
        join it."""
        subscriptions = super().create(vals_list)
        if not self.env.context.get('drip_subscription_mail_pending'):
            subscriptions._send_drip_subscription_mail()
        return subscriptions

    def _send_drip_subscription_mail(self):
        """Send the subscription template of their list to the contacts of
        these new subscriptions."""
        for subscription in self.filtered(
                lambda sub: sub.list_id.mail_contact and not sub.opt_out
                and not sub.contact_id.is_blacklisted):
            # Website visitors subscribe too: send as superuser
            mailing_list = subscription.list_id.sudo()
            mailing_list._send_drip_mail(
                mailing_list.template_id, subscription.contact_id)
