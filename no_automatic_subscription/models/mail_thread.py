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


class MailThread(models.AbstractModel):
    """ Stop automatic subscription """
    _inherit = 'mail.thread'

    def _get_no_subscription_models(self):
        """ This is used to return the model names to stop the automatic
         subscription. """
        if self.env.company.subscription_models_ids:
            return self.env.company.subscription_models_ids.mapped('model')
        return []

    def message_subscribe(self, partner_ids=None, subtype_ids=None, is_auto=True):
        """Add followers after checking subscription rules."""
        subscription_models = self._get_no_subscription_models()
        if subscription_models:
            for rec in self:
                if not is_auto:
                    return super(MailThread, self)._message_subscribe(
                        partner_ids, subtype_ids)
                elif rec._name not in subscription_models:
                    return super(MailThread, self)._message_subscribe(
                        partner_ids, subtype_ids)
        else:
            return super(MailThread, self)._message_subscribe(
                partner_ids, subtype_ids)

    def _message_auto_subscribe(self, updated_values,
                                followers_existing_policy='skip'):
        """Handle automatic subscription for allowed models."""
        subscription_models = self._get_no_subscription_models()
        if subscription_models:
            for rec in self:
                if rec._name not in subscription_models:
                    return super(MailThread, self)._message_auto_subscribe(
                        updated_values, followers_existing_policy)
        else:
            return super(MailThread, self)._message_auto_subscribe(
                updated_values, followers_existing_policy)

    def _message_auto_subscribe_notify(self, partner_ids, template):
        """Notify new followers using the configured template."""
        subscription_models = self._get_no_subscription_models()
        if subscription_models:
            for rec in self:
                if rec._name not in subscription_models:
                    return super(MailThread, self)._message_auto_subscribe_notify(
                        partner_ids, template)
        else:
            return super(MailThread, self)._message_auto_subscribe_notify(
                partner_ids, template)
