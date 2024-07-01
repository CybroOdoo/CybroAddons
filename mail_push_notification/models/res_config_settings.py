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
from firebase_admin import initialize_app, _apps
from firebase_admin import credentials
from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):
    """Inheriting the ResConfigSettings to add the firebase config details
        to push notifications """
    _inherit = 'res.config.settings'

    push_notification = fields.Boolean(string='Enable Push Notification',
                                       help="Enable Web Push Notification",
                                       related='company_id.push_notification',
                                       readonly=False)
    project_id_firebase = fields.Char(string="Project Id",
                                      help='Corresponding projectId of '
                                           'firebase config',
                                      related='company_id.project_id_firebase',
                                      readonly=False)
    private_key_ref = fields.Char(string='Private Key Id',
                                  help="Private Key Id in the certificate",
                                  related='company_id.private_key_ref',
                                  readonly=False)
    private_key = fields.Char(string="Private Key",
                              help="Private Key value in the firebase "
                                   "certificate",
                              related='company_id.private_key', readonly=False)
    client_email = fields.Char(string="Client Email", help='Client Email in '
                                                           'the firebase config',
                               related='company_id.client_email',
                               readonly=False)
    client_id_firebase = fields.Char(string="Client Id",
                                     help='Client Id in the firebase config',
                                     related='company_id.client_id_firebase',
                                     readonly=False)
    client_cert_url = fields.Char(string="Client Certificate Url",
                                  help='Value corresponding to '
                                       'client_x509_cert_url in the firebase '
                                       'config',
                                  related='company_id.client_cert_url',
                                  readonly=False)
    api_key = fields.Char(string="Api Key",
                          help='Corresponding apiKey of firebase config',
                          related='company_id.api_key', readonly=False)
    auth_domain = fields.Char(string="Auth Domain",
                              help='Corresponding authDomain of firebase '
                                   'config',
                              related='company_id.auth_domain', readonly=False)

    storage_bucket = fields.Char(string="Storage Bucket",
                                 help='Corresponding storageBucket of '
                                      'firebase config',
                                 related='company_id.storage_bucket',
                                 readonly=False)
    messaging_sender_id_firebase = fields.Char(string="Messaging Sender Id",
                                               help='Corresponding '
                                                    'messagingSenderId of '
                                                    'firebase config',
                                               related='company_id.messaging_sender_id_firebase',
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
    vapid = fields.Char(string="Vapid", help='VapId of the firebase',
                        related='company_id.vapid', readonly=False)

    def test_connection(self):
        """Test connection to firebase using the firebase credentials"""
        if not self.env.company.push_notification:
            return False
        try:
            # Initialize the firebase app with the credentials
            if not _apps:
                cred = credentials.Certificate(
                    {
                        "type": "service_account",
                        "project_id": self.project_id_firebase,
                        "private_key_id": self.private_key_ref,
                        "private_key": self.private_key.replace('\\n', '\n'),
                        "client_email": self.client_email,
                        "client_id": self.client_id_firebase,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_x509_cert_url": self.client_cert_url,
                        "universe_domain": "googleapis.com"
                    }
                )
                initialize_app(cred)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("Connection successfully established"),
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'message': _(
                        "Failed to connect with firebase:%s" % e),
                }
            }
