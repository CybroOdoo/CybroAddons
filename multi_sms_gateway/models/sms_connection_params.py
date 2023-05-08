# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
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
