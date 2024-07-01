# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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
from firebase_admin import messaging, initialize_app, credentials, _apps
from odoo import models


class MailThread(models.AbstractModel):
    """Inherits MailThread to send notifications using chatterbox"""
    _inherit = 'mail.thread'

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        """Override the _notify_thread() function to fetch chat message details
        and push that message as a notification."""
        res = super()._notify_thread(message, msg_vals=msg_vals, **kwargs)
        msg = message.read()
        if (self.env.company.push_notification and
                self.env.user.has_group('base.group_user')):
            try:
                domain = []
                receiver_ids = self._get_receiver_ids(msg)
                user_list = [rec.id for rec in receiver_ids]
                if receiver_ids:
                    domain = [('user_id', 'in', user_list)]
                self._send_push_notification(msg, domain)
            except Exception as e:
                self.env['ir.logging'].sudo().create({
                    'name': 'Push Notification Error',
                    'type': 'server',
                    'level': 'ERROR',
                    'message': str(e),
                    'path': 'mail.thread',
                    'func': '_notify_thread',
                    'line': '45',
                })
        return res

    def _get_receiver_ids(self, msg):
        """Identify the receiver of the notification."""
        receiver_ids = []
        receiver_id = False
        if self.channel_type != 'channel':
            for partner in self.channel_partner_ids:
                if partner.id != msg[0]['author_id'][0]:
                    receiver_id = self.env['res.users'].search(
                        [('partner_id', '=', partner.id)])
                if receiver_id:
                    receiver_ids.append(receiver_id)
        else:
            for partner in self.channel_partner_ids:
                receiver_id = self.env['res.users'].search(
                    [('partner_id', '=', partner.id)])
                if receiver_id:
                    receiver_ids.append(receiver_id)
        return receiver_ids

    def _send_push_notification(self, msg, domain):
        """Send a push notification using Firebase."""
        if not _apps:
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": self.env.company.project_id_firebase,
                "private_key_id": self.env.company.private_key_ref,
                "private_key": self.env.company.private_key.replace('\\n',
                                                                    '\n'),
                "client_email": self.env.company.client_email,
                "client_id": self.env.company.client_id_firebase,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": self.env.company.client_cert_url,
                "universe_domain": "googleapis.com"
            })
            initialize_app(cred)
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title='Message from ' + msg[0]['author_id'][1],
                body=msg[0]['body']
            ),
            tokens=[reg_id.register_id for reg_id in
                    self.env['push.notification'].search(domain)]
        )
        messaging.send_each_for_multicast(message)
