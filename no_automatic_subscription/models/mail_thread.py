"""Automatic subscription"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    """Stop automatic subscription"""
    _inherit = 'mail.thread'

    def message_subscribe(self, partner_ids=None, subtype_ids=None):
        """ Main public API to add followers to a record set. Its main purpose
         is to perform access rights checks before calling `
         `_message_subscribe``. """
        subscription_models = self.no_subscription()
        if subscription_models:
            for rec in self:
                if rec._name not in subscription_models:
                    return super(MailThread, self)._message_subscribe(
                        partner_ids, subtype_ids)
        else:
            return super(MailThread, self)._message_subscribe(
                partner_ids, subtype_ids)

    def _message_auto_subscribe(self, updated_values,
                                followers_existing_policy='skip'):
        """ Handle auto subscription. Auto subscription is done based on two
                main mechanisms
                 * using subtypes parent relationship. For example following a
                 parent record (i.e. project) with subtypes linked to child
                 records (i.e. task). See mail.message.subtype ``
                 _get_auto_subscription_subtypes``;
                 * calling _message_auto_subscribe_notify that returns
                 a list of partner to subscribe, as well as data about the
                 subtypes and notification to send. Base behavior is to
                 subscribe responsible and notify them; Adding
                 application-specific auto subscription should be done
                 by overriding``_message_auto_subscribe_followers``.
                 It should return structured data for new partner to subscribe,
                 with subtypes and eventual notification to perform. See that
                 method for more details.
                :param updated_values: values modifying the record trigerring
                auto subscription
                """
        model_name = self.no_subscription()
        if model_name:
            for rec in self:
                if rec._name not in model_name:
                    return super(MailThread, self)._message_auto_subscribe(
                        updated_values, followers_existing_policy)
        else:
            return super(MailThread, self)._message_auto_subscribe(
                updated_values, followers_existing_policy)

    def _message_auto_subscribe_notify(self, partner_ids, template):
        """ Notify new followers, using a template to render the content of the
               notification message. Notifications pushed are done using the
               standard
               notification mechanism in mail.thread. It is  inbox either email
               depending on the partner state: no user (email, customer), share
               user
               (email, customer) or classic user (notification_type)

               :param partner_ids: IDs of partner to notify;
               :param template: XML ID of template used for the notification;
               """
        model_to_stop_subscription = self.no_subscription()
        if model_to_stop_subscription:
            for rec in self:
                if  rec._name not in model_to_stop_subscription:
                    return super(MailThread, self)._message_auto_subscribe_notify(
                        partner_ids, template)
        else:
            return super(MailThread, self)._message_auto_subscribe_notify(
                partner_ids, template)

    def no_subscription(self):
        """This is used to return the model names to stop the automatic
         subscription"""
        subscription_models = self.env[
            'ir.config_parameter'].sudo().get_param(
            'no_automatic_subscription.subscription_models_ids')
        if subscription_models:
            subscription = subscription_models.replace('[', '')
            subscription_change = subscription.replace(']', '')
            subscription_models_ids = []
            for rec in subscription_change.split(','):
                if int(rec):
                    model_subscription = self.env['ir.model'].browse(int(rec))
                    subscription_models_ids.append(model_subscription.model)
            return subscription_models_ids
