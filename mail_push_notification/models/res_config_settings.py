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
from pyfcm import FCMNotification
from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):
    """Inheriting the ResConfigSettings to add the firebase config details
        to push notifications """
    _inherit = 'res.config.settings'

    push_notification = fields.Boolean(string='Enable Push Notification',
                                       help="Enable Web Push Notification",
                                       related='company_id.push_notification',
                                       readonly=False)
    server_key = fields.Char(string="Server Key",
                             help="Server Key of the firebase",
                             related='company_id.server_key', readonly=False)
    vapid = fields.Char(string="Vapid", help='VapId of the firebase',
                        related='company_id.vapid', readonly=False)
    api_key = fields.Char(string="Api Key",
                          help='Corresponding apiKey of firebase config',
                          related='company_id.api_key', readonly=False)
    auth_domain = fields.Char(string="Auth Domain",
                              help='Corresponding authDomain of firebase '
                                   'config',
                              related='company_id.auth_domain', readonly=False)
    project_id_firebase = fields.Char(string="Project Id",
                                      help='Corresponding projectId of '
                                           'firebase config',
                                      related='company_id.project_id_firebase',
                                      readonly=False)
    storage_bucket = fields.Char(string="Storage Bucket",
                                 help='Corresponding storageBucket of '
                                      'firebase config',
                                 related='company_id.storage_bucket',
                                 readonly=False)
    messaging_sender_id_firebase = fields.Char(string="Messaging Sender Id",
                                               help='Corresponding '
                                                    'messagingSenderId of '
                                                    'firebase config',
                                               related='company_id'
                                                       '.messaging_sender_id_firebase',
                                               readonly=False)
    app_id_firebase = fields.Char(string="App Id",
                                  help='Corresponding appId of firebase config',
                                  related='company_id.app_id_firebase',
                                  readonly=False)
    measurement_id_firebase = fields.Char(string="Measurement Id",
                                          help='Corresponding measurementId '
                                               'of firebase config',
                                          related='company_id'
                                                  '.measurement_id_firebase',
                                          readonly=False)

    def test_connection(self):
        """Test connection to firebase using the firebase credentials"""
        if self.env.company.push_notification:
            try:
                push_service = FCMNotification(
                    api_key=self.env.company.server_key)
                registration_ids = self.env['push.notification'].sudo().search(
                    [('user_id', '=', self.env.user.id)])
                push_service.notify_multiple_devices(
                    registration_ids=[registration_id.register_id for
                                      registration_id in registration_ids],
                    message_title='Test Connection',
                    message_body='Successfully',
                    extra_notification_kwargs={
                        'click_action': '/web'
                    })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'success',
                        'message': _("Connection successfully established"),
                        'next': {
                            'type': 'ir.actions.client',
                            'tag': 'reload_context',
                        },
                    }
                }
            except:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'danger',
                        'message': _(
                            "Failed to connect with firebase"),
                        'next': {
                            'type': 'ir.actions.client',
                            'tag': 'reload_context',
                        },
                    }
                }
