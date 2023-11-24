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
from odoo import fields, models


class ResCompany(models.Model):
    """Inheriting this class to add the firebase credential need in config
            settings and use the multi company feature"""
    _inherit = 'res.company'

    push_notification = fields.Boolean(string='Enable Push Notification',
                                       help="Enable Web Push Notification")
    server_key = fields.Char(string="Server Key",
                             help="Server Key of the firebase")
    vapid = fields.Char(string="Vapid", help='VapId of the firebase',
                        readonly=False)
    api_key = fields.Char(string="Api Key",
                          help='Corresponding apiKey of firebase config',
                          readonly=False)
    auth_domain = fields.Char(string="Auth Domain",
                              help='Corresponding authDomain of firebase '
                                   'config')
    project_id_firebase = fields.Char(string="Project Id",
                                      help='Corresponding projectId of '
                                           'firebase config')
    storage_bucket = fields.Char(string="Storage Bucket",
                                 help='Corresponding storageBucket of '
                                      'firebase config')
    messaging_sender_id_firebase = fields.Char(string="Messaging Sender Id",
                                               help='Corresponding '
                                                    'messagingSenderId of '
                                                    'firebase config')
    app_id_firebase = fields.Char(string="App Id",
                                  help='Corresponding appId of firebase config')
    measurement_id_firebase = fields.Char(string="Measurement Id",
                                          help='Corresponding measurementId '
                                               'of firebase config')
