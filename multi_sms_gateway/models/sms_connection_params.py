# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################

""" This module helps to Connect SMS gateway. """
from odoo import fields, models


class SmsConnectionParams(models.Model):
    """
    Class to add the credentials for establishing the connection with the
    gateways.
    """
    _name = 'sms.connection.params'
    _description = 'SMS Connection'

    name = fields.Char(string='Name', help='Name for the parameter.')
    sms_gateway_config_id = fields.Many2one(
        'sms.gateway.config', string='Connection ID',
        help='Gateway configuration with credentials.')
    connection_api = fields.Char(
        string='API Method', help='Enter the API method.')
    connection_value = fields.Char(
        string='Value', help='Connection value for the gateway.')
